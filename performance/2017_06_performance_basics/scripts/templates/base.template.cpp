#include <algorithm>
#include <iostream>
#include <string>
#include <time.h>
#include <sstream>

using namespace std;


int main(void) {
    const int N={{ array_size }}, M={{ array_size }};
    int start, end;
    double ** C;
    double ** A;
    double ** B;
    double num = 0.0;

    string input;

    // Allocate arrays
    C = new double*[N];
    A = new double*[N];
    B = new double*[N];
    for (int q = 0; q < M; q++)
        C[q] = new double[N];
    for (int r = 0; r < M; r++)
        A[r] = new double[N];
    for (int s = 0; s < M; s++)
        B[s] = new double[N];

    // Get user input (stops compiler optimising this away)
    cout << "Enter a number: ";
    getline(cin, input);
    stringstream input_stream(input);
    input_stream >> num;

    cout << "Initialising...";
    for (int a = 0; a < N; a++) {
        for (int b = 0; b < N; b++) {
            C[a][b] = num;
            A[a][b] = num * 2.0;
            B[a][b] = num * 3.0;
        }
    }
    cout << "complete." << endl;


    // Perform MMM
    cout << "Calculating..." << endl;
    start = clock();

    {% block mmm_loop %}
    {% endblock %}

    end = clock();

    cout << "Clocks: " << end - start << endl;

    return 0;
}

