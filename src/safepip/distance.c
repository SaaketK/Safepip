#include <string.h>
#include <stdlib.h>

#define MIN3(a, b, c) ((a) < (b) ? ((a) < (c) ? (a) : (c)) : ((b) < (c) ? (b) : (c)))

// This function will be exported to Python
// levenshtein distance calculator
int levenshtein(const char *s1, const char *s2) {
    int len1 = strlen(s1);
    int len2 = strlen(s2);

    // Create two rows for the DP table
    int *prev_row = (int *)malloc((len2 + 1) * sizeof(int));
    int *curr_row = (int *)malloc((len2 + 1) * sizeof(int));

    for (int j = 0; j <= len2; j++) prev_row[j] = j;

    for (int i = 1; i <= len1; i++) {
        curr_row[0] = i;
        for (int j = 1; j <= len2; j++) {
            int cost = (s1[i - 1] == s2[j - 1]) ? 0 : 1;
            curr_row[j] = MIN3(
                curr_row[j - 1] + 1,     // insertion
                prev_row[j] + 1,         // deletion
                prev_row[j - 1] + cost   // substitution
            );
        }
        // Swap rows
        for (int j = 0; j <= len2; j++) prev_row[j] = curr_row[j];
    }

    int result = prev_row[len2];
    free(prev_row);
    free(curr_row);
    return result;
}