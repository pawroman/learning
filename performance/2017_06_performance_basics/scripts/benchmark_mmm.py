#!/usr/bin/env python3

import itertools
import logging
import pathlib
import subprocess
import tempfile

from typing import Dict, List

import jinja2
import pandas as pd


TEMPLATE_PATH = str((pathlib.Path(__file__).parent / "templates").resolve())
TEMPLATE_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_PATH)
)

LOOP_VARS = ("i", "j", "k")

# TODO: make this configurable / auto-discover the compiler
COMPILER_COMMAND = "c++"


def get_compiler_version_info() -> str:
    version_output = subprocess.check_output([COMPILER_COMMAND, "--version"])
    version_line = version_output.splitlines()[0]

    return str(version_line, encoding="ascii")


def benchmark_naive(optimization_level=0, num_runs=6, seed_value=5.5) -> Dict[str, List[int]]:
    template = TEMPLATE_ENV.get_template("naive.cpp.j2")
    results = {}

    logging.info("Benchmarking naive looping with opt level=%s, %s runs per permutation, seed value=%s",
                 optimization_level, num_runs, seed_value)

    for var_names in itertools.permutations(LOOP_VARS):
        rendered = template.render(var1=var_names[0], var2=var_names[1], var3=var_names[2])

        logging.info("Benchmarking permutation: %s %s %s", *var_names)

        permutation_results = compile_and_benchmark(rendered, optimization_level, num_runs, seed_value)
        results[" ".join(var_names)] = permutation_results

    return results


def benchmark_block_tiling(var_names, block_size, optimization_level=0, num_runs=6, seed_value=5.5) -> List[int]:
    template = TEMPLATE_ENV.get_template("block_tiled.cpp.j2")

    logging.info("Benchmarking block tiling with variables: %s, block size=%s, opt level=%s, %s runs, seed value=%s",
                 var_names, block_size, optimization_level, num_runs, seed_value)

    rendered = template.render(var1=var_names[0], var2=var_names[1], var3=var_names[2],
                               block_size=block_size)

    return compile_and_benchmark(rendered, optimization_level, num_runs, seed_value)


def benchmark_double_block_tiling(var_names, block_size, second_block_size,
                                  optimization_level=0, num_runs=6, seed_value=5.5) -> List[int]:
    template = TEMPLATE_ENV.get_template("double_block_tiled.cpp.j2")

    logging.info("Benchmarking double block tiling with variables: %s, block sizes: %s/%s,"
                 " opt level=%s, %s runs, seed value=%s",
                 var_names, block_size, second_block_size, optimization_level, num_runs, seed_value)

    rendered = template.render(var1=var_names[0], var2=var_names[1], var3=var_names[2],
                               block_size=block_size, second_block_size=second_block_size)

    return compile_and_benchmark(rendered, optimization_level, num_runs, seed_value)


def compile_and_benchmark(cpp_source, optimization_level, num_runs, seed_value) -> List[int]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        src_path = str(tmp_path / "source.cpp")
        out_path = str(tmp_path / "binary_out")

        with open(src_path, "w") as f:
            f.write(cpp_source)

        compile_args = (COMPILER_COMMAND, src_path, "-O" + str(optimization_level),
                        "-o", out_path)
        subprocess.check_call(compile_args)

        input_bytes = bytes(str(seed_value) + "\n", "ascii")
        results = []

        for _ in range(num_runs):
            output = subprocess.check_output(out_path, input=input_bytes)
            value = parse_clocks(output)
            results.append(value)

    return results


def parse_clocks(output: bytes) -> int:
    encoded_output = str(output, encoding="ascii")
    split = encoded_output.rsplit("Clocks: ", 1)
    value_str = split[-1]

    return int(value_str)


def main():
    logging.info("Compiler version: %s", get_compiler_version_info())

    naive_results = benchmark_naive()
    print(naive_results)


def setup_logging():
    default_log_format = "[%(asctime)-15s] [%(levelname)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=default_log_format)


if __name__ == "__main__":
    setup_logging()
    main()

