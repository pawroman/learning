{% extends "base.cpp.j2" %}

{# block-tiled implementation with configurable variables and block size #}

{% block mmm_loop %}
const int block_size = {{ block_size }};
const int second_block_size = {{ second_block_size }};

// Outer loop, optimised for RAM access.
for (int {{ outer_vars[0] }} = 0; {{ outer_vars[0] }} < N; {{ outer_vars[0] }} += block_size) {
    for (int {{ outer_vars[1] }} = 0; {{ outer_vars[1] }} < N; {{ outer_vars[1] }} += block_size) {
        for (int {{ outer_vars[2] }} = 0; {{ outer_vars[2] }} < N; {{ outer_vars[2] }} += block_size) {

            // CPU Cache optimisation
            for (int ii = {{ inner_vars[0] }}; ii < ({{ inner_vars[0] }} + block_size); ii += second_block_size) {
                for (int kk = {{ inner_vars[1] }}; kk < ({{ inner_vars[1] }} + block_size); kk += second_block_size) {
                    for (int jj = {{ inner_vars[2] }}; jj < ({{ inner_vars[2] }} + block_size); jj += second_block_size) {

                        // CPU Register optimisation
                        for (int kkk = {{ innermost_vars[0] }}; kkk < ({{ innermost_vars[0] }} + second_block_size); kkk++) {
                            for (int jjj = {{ innermost_vars[1] }}; jjj < ({{ innermost_vars[1] }} + second_block_size); jjj++) {
                                for (int iii = {{ innermost_vars[2] }}; iii < ({{ innermost_vars[2] }} + second_block_size); iii++) {
                                    C[iii][jjj] += A[iii][kkk] * B[kkk][jjj];
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
{% endblock %}
