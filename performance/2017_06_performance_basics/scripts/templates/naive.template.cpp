{% extends "base.template.cpp" %}

{# naive mmm implementation with configurable variables #}

{% block mmm_loop %}
for (int {{ var_names[0] }} = 0; {{ var_names[0] }} < N; {{ var_names[0] }}++) {
    for (int {{ var_names[1] }} = 0; {{ var_names[1] }} < N; {{ var_names[1] }}++) {
        for (int {{ var_names[2] }} = 0; {{ var_names[2] }} < N; {{ var_names[2] }}++) {
            C[i][j] += A[i][k] * B[k][j];
        }
    }
}
{% endblock %}
