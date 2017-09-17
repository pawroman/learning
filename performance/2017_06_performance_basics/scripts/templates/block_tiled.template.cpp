{% extends "base.template.cpp" %}

{# block-tiled implementation with configurable variables and block size #}

{% block mmm_loop %}
const int block_size = {{ block_size }};

for (int {{ outer_vars[0] }} = 0; {{ outer_vars[0] }} < N; {{ outer_vars[0] }} += block_size) {
    for (int {{ outer_vars[1] }} = 0; {{ outer_vars[1] }} < N; {{ outer_vars[1] }} += block_size) {
        for (int {{ outer_vars[2] }} = 0; {{ outer_vars[2] }} < N; {{ outer_vars[2] }} += block_size) {

            for (int ii = {{ inner_vars[0] }}; ii < min(N, {{ inner_vars[0] }} + block_size); ii++) {
                for (int kk = {{ inner_vars[1] }}; kk < min(N, {{ inner_vars[1] }} + block_size); kk++) {
                    for (int jj = {{ inner_vars[2] }}; jj < min(N, {{ inner_vars[2] }} + block_size); jj++) {
                        C[ii][jj] += A[ii][kk] * B[kk][jj];
                    }
                }
            }
        }
    }
}

{% endblock %}
