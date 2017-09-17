#!/usr/bin/env python3

import itertools
import logging
import pathlib
import subprocess
import tempfile

from collections import defaultdict
from typing import Dict, List, Sequence, Mapping

import jinja2
import pandas as pd


class BenchmarkMMM:
    LOOP_VARS = ("i", "j", "k")
    COMPILER_COMMAND = "c++"

    TEMPLATE_PATH = str((pathlib.Path(__file__).parent / "templates").resolve())
    TEMPLATE_ENV = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_PATH)
    )

    def __init__(self, array_size=1000, optimization_level=0, seed_value=5.5):
        self.array_size = array_size
        self.optimization_level = optimization_level
        self.seed_value = seed_value

        # TODO: make this configurable / auto-discover the compiler
        self.compiler_command = self.COMPILER_COMMAND

    def get_compiler_version_info(self) -> str:
        version_output = subprocess.check_output([self.compiler_command, "--version"])
        version_line = version_output.splitlines()[0]

        return str(version_line, encoding="ascii")

    def get_template(self, name):
        return self.TEMPLATE_ENV.get_template(name)

    def benchmark_naive(self, num_runs=6, optimization_level=None,
                        extra_compiler_args=()) -> pd.DataFrame:
        template = self.get_template("naive.template.cpp")
        results_dict = {}

        if optimization_level is None:
            optimization_level = self.optimization_level

        logging.info("Benchmarking naive looping: array size %s, opt level %s,"
                     " %s runs per permutation",
                     self.array_size, optimization_level, num_runs)

        for var_names in self.get_vars_permutations(1):
            rendered = template.render(array_size=self.array_size, var_names=var_names)

            logging.info("Benchmarking permutation: %s", var_names)
            permutation_results = self.compile_and_benchmark(
                rendered, optimization_level, num_runs, self.seed_value, extra_compiler_args
            )

            results_dict[" ".join(var_names)] = permutation_results

        df = pd.DataFrame(results_dict, index=range(1, len(results_dict) + 1))

        return (
            df.rename_axis("Run number")
              .rename_axis("Permutation", axis="columns")
        )

    def benchmark_block_tiling(self, num_runs=3, optimization_level=0, extra_compiler_args=(),
                               block_size_samples=40, outer=None, inner=None) -> pd.DataFrame:
        template = self.get_template("block_tiled.template.cpp")
        results_dict = defaultdict(dict)

        if optimization_level is None:
            optimization_level = self.optimization_level

        logging.info("Benchmarking block tiling: array size %s, opt level %s,"
                     " %s runs per permutation, %s block size samples",
                     self.array_size, optimization_level, num_runs, block_size_samples)

        sizes = self.get_block_size_samples(block_size_samples)

        for block_size in sizes:
            logging.info("Benchmarking outer/inner permutations: block size: %s", block_size)

            for outer_vars, inner_vars in self.get_vars_permutations(2, outer, inner):
                rendered = template.render(
                    array_size=self.array_size, block_size=block_size,
                    outer_vars=outer_vars, inner_vars=inner_vars
                )

                permutation_results = self.compile_and_benchmark(
                    rendered, optimization_level, num_runs, self.seed_value,
                    extra_compiler_args=extra_compiler_args
                )

                sub_key = "{} / {}".format(" ".join(outer_vars), " ".join(inner_vars))
                results_dict[block_size][sub_key] = permutation_results

        # Index: Block size / Run number (starting from 1)
        # Columns: Permutations

        df = pd.concat([pd.DataFrame(inner, index=range(1, num_runs + 1))
                        for inner in results_dict.values()],
                       keys=results_dict.keys())

        return (
            df.rename_axis(["Block size", "Run number"])
              .rename_axis("Permutation", axis="columns")
        )

    # def benchmark_double_block_tiling(self, var_names, block_size, second_block_size,
    #                                   optimization_level=0, num_runs=6, seed_value=5.5) -> List[
    #     int]:
    #     template = TEMPLATE_ENV.get_template("double_block_tiled.template.cpp")
    #
    #     logging.info("Benchmarking double block tiling with variables: %s, block sizes: %s/%s,"
    #                  " opt level=%s, %s runs, seed value=%s",
    #                  var_names, block_size, second_block_size, optimization_level, num_runs,
    #                  seed_value)
    #
    #     rendered = template.render(var1=var_names[0], var2=var_names[1], var3=var_names[2],
    #                                block_size=block_size, second_block_size=second_block_size)
    #
    #     return self.compile_and_benchmark(rendered, optimization_level, num_runs, seed_value)

    @classmethod
    def get_vars_permutations(cls, nest_levels, *level_permutations):
        levels = []

        for _, level_perms in itertools.zip_longest(range(nest_levels), level_permutations):
            if not level_perms:
                level_perms = itertools.permutations(cls.LOOP_VARS)

            levels.append(level_perms)

        if len(levels) == 1:
            yield from levels[0]
        else:
            yield from itertools.product(*levels)

    def get_block_size_samples(self, samples):
        step = self.array_size // samples

        sizes = list(range(step, self.array_size + 1, step))

        if sizes[-1] != self.array_size:
            sizes.append(self.array_size)

        return sizes

    def compile_and_benchmark(self, cpp_source, optimization_level, num_runs, seed_value,
                              extra_compiler_args=()) -> List[int]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            src_path = str(tmp_path / "source.cpp")
            out_path = str(tmp_path / "binary_out")

            with open(src_path, "w") as f:
                f.write(cpp_source)

            compile_args = (self.compiler_command, src_path, "-O" + str(optimization_level),
                            "-o", out_path, *extra_compiler_args)

            try:
                subprocess.check_output(compile_args, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as err:
                # log compiler error
                logging.error(err.output)
                raise

            input_bytes = bytes(str(seed_value) + "\n", "ascii")
            results = []

            for _ in range(num_runs):
                output = subprocess.check_output(out_path, input=input_bytes)
                value = self.parse_clocks(output)
                results.append(value)

        return results

    @classmethod
    def parse_clocks(cls, output: bytes) -> int:
        encoded_output = str(output, encoding="ascii")
        split = encoded_output.rsplit("Clocks: ", 1)
        value_str = split[-1]

        return int(value_str)


def setup_logging():
    default_log_format = "[%(asctime)-15s] [%(levelname)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=default_log_format)


if __name__ == "__main__":
    setup_logging()

