-- BugYou Sample Challenges Data
-- Run this AFTER database_setup.sql to populate tables with sample challenges
-- This ensures new users have challenges to work on

-- Generated automatically from existing database
-- Generated on: 2025-07-05 15:51:01

-- PYTHON_BASIC CHALLENGES
-- 1 challenges

INSERT INTO python_basic (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (1, 'Fix the Average Calculator', 'A function to calculate averages has a division by zero bug. Multiple solutions are valid!', 'Fix the buggy calculate_average function that crashes when given an empty list. Any approach that handles empty lists properly is acceptable.', 'def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    # Bug: Division by zero when list is empty!
    return total / len(numbers)', 'def calculate_average(numbers):
    if len(numbers) == 0:
        return 0  # One possible approach
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)', 'This is just ONE way to fix it. You could also return None, raise an exception, or use other approaches as long as the test cases pass.', 'What happens when you divide by zero? Check if the list is empty first!', 'You could return 0, return None, or handle it differently - just make sure your output matches the expected results.', 'There are multiple valid ways to fix this. Choose the approach that makes sense to you.', 'Learn about edge case handling and multiple solution approaches. Understand that programming problems often have many valid solutions.', 'Students often think there''s only one "correct" way to fix a bug. In reality, multiple approaches can work.', 'Test your solution with the given test cases. As long as your output matches the expected output, your solution is valid!', 10, 15, '[1, 2, 3, 4, 5]', '3.0', 'Standard case with multiple numbers', 1, '[10, 20]', '15.0', 'Simple case with two numbers', 1, '[]', '0', 'Edge case: empty list should return 0', 2, NULL, NULL, NULL, 1, NULL, NULL, NULL, 1, '[0, 0, 0]', '0.0', 'Hidden validation test', '[-1, 1]', '0.0', 'Hidden edge case', 'exact', 0.000001, 2025-07-04 16:47:21.799786, NULL, true, 0, 0.00, 0.00);

-- PYTHON_INTERMEDIATE CHALLENGES
-- 1 challenges

INSERT INTO python_intermediate (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, alternative_approaches, hint_1, hint_2, hint_3, hint_4, learning_objectives, prerequisites, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, hidden_test_3_input, hidden_test_3_expected, hidden_test_3_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (1, 'Binary Search Bug Hunter', 'Find and fix the bug in this binary search implementation that causes incorrect results.', 'This binary search function should find the index of a target value in a sorted array. However, it contains a subtle bug that causes it to return incorrect results in certain cases. Your task is to identify and fix the bug while maintaining the O(log n) time complexity.', 'def binary_search(arr, target):
    left = 0
    right = len(arr)  # BUG: Should be len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Test the function
print(binary_search([1, 3, 5, 7, 9, 11], 7))', 'def binary_search(arr, target):
    left = 0
    right = len(arr) - 1  # FIXED: Subtract 1 for correct indexing
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Test the function
print(binary_search([1, 3, 5, 7, 9, 11], 7))', 'The bug was in the initialization of ''right''. It should be len(arr) - 1, not len(arr), because array indices are 0-based. Setting right = len(arr) causes an index out of bounds error when accessing arr[mid].', NULL, 'Look carefully at the array indexing. What is the valid range of indices for an array?', 'Consider what happens when mid equals len(arr) - 1. Is arr[mid] a valid access?', 'Remember that array indices go from 0 to length-1, not 0 to length.', NULL, 'Understand array indexing, boundary conditions in algorithms, and binary search implementation details.', NULL, 'Off-by-one errors in array bounds, incorrect loop termination conditions.', 'Always double-check array bounds when working with indices. Test with edge cases like single-element arrays.', 15, 25, '[1, 3, 5, 7, 9, 11], 7', '3', 'Find element in middle of array', 1, '[1, 3, 5, 7, 9, 11], 1', '0', 'Find first element', 2, '[1, 3, 5, 7, 9, 11], 11', '5', 'Find last element', 2, '[1, 3, 5, 7, 9, 11], 4', '-1', 'Element not found', 1, '[5], 5', '0', 'Single element array', 2, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden performance test', NULL, NULL, 'Hidden edge case', 'exact', 0.000001, 2025-07-05 14:01:30.042758, NULL, true, 0, 0.00, 0.00);

-- PYTHON_ADVANCED CHALLENGES
-- 1 challenges

INSERT INTO python_advanced (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, alternative_approaches, algorithm_explanation, hint_1, hint_2, hint_3, hint_4, hint_5, learning_objectives, prerequisites, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, hidden_test_3_input, hidden_test_3_expected, hidden_test_3_description, hidden_test_4_input, hidden_test_4_expected, hidden_test_4_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (1, 'Dijkstra''s Algorithm Debugger', 'Debug this implementation of Dijkstra''s shortest path algorithm that produces incorrect results.', 'This implementation of Dijkstra''s algorithm should find the shortest path from a source vertex to all other vertices in a weighted graph. However, it contains multiple subtle bugs that cause incorrect shortest path calculations. Your task is to identify and fix all bugs while maintaining the algorithm''s correctness and O((V + E) log V) complexity.', 'import heapq

def dijkstra(graph, start):
    distances = {node: float(''inf'') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    visited = set()
    
    while pq:
        current_distance, current = heapq.heappop(pq)
        
        # BUG 1: Not checking if already visited
        # if current in visited:
        #     continue
        visited.add(current)
        
        for neighbor, weight in graph[current]:
            distance = current_distance + weight
            
            # BUG 2: Wrong comparison operator
            if distance > distances[neighbor]:  # Should be <
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

# Test case
graph = {
    ''A'': [(''B'', 4), (''C'', 2)],
    ''B'': [(''C'', 1), (''D'', 5)], 
    ''C'': [(''D'', 8), (''E'', 10)],
    ''D'': [(''E'', 2)],
    ''E'': []
}

print(dijkstra(graph, ''A''))', 'import heapq

def dijkstra(graph, start):
    distances = {node: float(''inf'') for node in graph}
    distances[start] = 0
    pq = [(0, start)]
    visited = set()
    
    while pq:
        current_distance, current = heapq.heappop(pq)
        
        # FIXED: Check if already visited to avoid reprocessing
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor, weight in graph[current]:
            distance = current_distance + weight
            
            # FIXED: Correct comparison for shortest path
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor))
    
    return distances

# Test case
graph = {
    ''A'': [(''B'', 4), (''C'', 2)],
    ''B'': [(''C'', 1), (''D'', 5)], 
    ''C'': [(''D'', 8), (''E'', 10)],
    ''D'': [(''E'', 2)],
    ''E'': []
}

print(dijkstra(graph, ''A''))', 'Two critical bugs: 1) Missing visited check causes nodes to be processed multiple times, leading to incorrect distances. 2) Wrong comparison operator (> instead of <) causes the algorithm to find longest paths instead of shortest paths.', NULL, NULL, 'Dijkstra''s algorithm should find the SHORTEST path. Check your comparison operators carefully.', 'Once a node is visited and its shortest distance is determined, it should not be processed again.', 'The priority queue might contain multiple entries for the same node. How do you handle this?', NULL, NULL, 'Master advanced graph algorithms, understand priority queue usage, and learn complex debugging techniques.', NULL, 'Incorrect comparison operators, missing visited checks, wrong data structure usage.', 'Complex algorithms require systematic debugging. Test each component separately and verify the algorithm''s invariants.', 20, 35, '{''A'': [(''B'', 1)], ''B'': []}, ''A''', '{''A'': 0, ''B'': 1}', 'Simple two-node graph', 1, '{''A'': [(''B'', 4), (''C'', 2)], ''B'': [(''C'', 1), (''D'', 5)], ''C'': [(''D'', 8), (''E'', 10)], ''D'': [(''E'', 2)], ''E'': []}, ''A''', '{''A'': 0, ''B'': 3, ''C'': 2, ''D'': 8, ''E'': 10}', 'Complex graph with multiple paths', 3, '{''A'': [(''B'', 1), (''C'', 4)], ''B'': [(''C'', 2), (''D'', 5)], ''C'': [(''D'', 1)], ''D'': []}, ''A''', '{''A'': 0, ''B'': 1, ''C'': 3, ''D'': 4}', 'Alternative shorter path exists', 3, '{''X'': []}, ''X''', '{''X'': 0}', 'Single node graph', 1, '{''A'': [(''B'', 10), (''C'', 3)], ''B'': [(''C'', 1), (''D'', 2)], ''C'': [(''B'', 4), (''D'', 8)], ''D'': []}, ''A''', '{''A'': 0, ''B'': 7, ''C'': 3, ''D'': 9}', 'Graph with bidirectional paths', 4, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden performance test', NULL, NULL, 'Hidden edge case', NULL, NULL, 'Hidden stress test', 'exact', 0.000001, 2025-07-05 14:01:32.188723, NULL, true, 0, 0.00, 0.00);

-- CPP_BASIC CHALLENGES
-- 2 challenges

INSERT INTO cpp_basic (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (2, 'Fix the Max Product', 'Find and fix the bug in the function that calculates the maximum product of two adjacent elements in an array.', 'The maxProduct function should find the maximum product of two adjacent elements in an array, but it fails when all products are negative.', '#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int maxProduct(vector<int> arr) {
    int maxProd = 0;  // Bug: Wrong initialization for negative numbers!
    
    for (int i = 0; i < arr.size() - 1; i++) {
        int product = arr[i] * arr[i + 1];
        maxProd = max(maxProd, product);
    }
    
    return maxProd;
}', '#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int maxProduct(vector<int> arr) {
    if (arr.size() < 2) return 0;
    
    int maxProd = arr[0] * arr[1];  // Initialize with first product
    
    for (int i = 1; i < arr.size() - 1; i++) {
        int product = arr[i] * arr[i + 1];
        maxProd = max(maxProd, product);
    }
    
    return maxProd;
}', 'Initialize maxProd with the first valid product instead of 0 to handle negative numbers correctly.', 'What happens when you initialize maxProd to 0 but all products are negative?', 'Try initializing maxProd with the first product instead of 0.', 'Think about edge cases: what if the array has less than 2 elements?', 'Learn about proper variable initialization and handling edge cases with negative numbers.', 'Students often initialize with 0 without considering that all valid results might be negative.', 'Consider what happens when all products are negative. Zero initialization won''t work!', 10, 15, '[2, 3, 1, 4]', '6', 'Standard case with positive numbers', 1, '[-1, -2, -3, -4]', '12', 'All negative numbers - maximum product should be 12 (-3 * -4)', 2, '[5, -2, 3]', '-6', 'Mixed positive/negative - maximum is -6 (-2 * 3)', 2, NULL, NULL, NULL, 1, NULL, NULL, NULL, 1, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden edge case', 'exact', 0.000001, 2025-07-04 18:58:57.177683, NULL, true, 0, 0.00, 0.00);
INSERT INTO cpp_basic (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (1, 'Fix the Array Sum Calculator', 'The calculateSum function has an off-by-one error that causes array index out of bounds. Fix the bug so it correctly sums all elements in the vector.', 'This function should calculate the sum of all elements in a vector, but it has an off-by-one error in the loop condition that causes index out of bounds errors.', '#include <iostream>
#include <vector>
using namespace std;

int calculateSum(vector<int> numbers) {
    int sum = 0;
    // Bug: Off-by-one error in loop condition!
    for (int i = 0; i <= numbers.size(); i++) {
        sum += numbers[i];
    }
    return sum;
}', '#include <iostream>
#include <vector>
using namespace std;

int calculateSum(vector<int> numbers) {
    int sum = 0;
    // Fix: Use < instead of <= to avoid out of bounds
    for (int i = 0; i < numbers.size(); i++) {
        sum += numbers[i];
    }
    return sum;
}

int main() {
    cout << "Function ready for testing" << endl;
    return 0;
}', 'Change <= to < in the loop condition. Arrays/vectors are zero-indexed.', 'Look at the loop condition. What happens when i equals numbers.size()?', 'Arrays/vectors are zero-indexed. If size is 5, valid indices are 0-4, not 0-5!', 'Change <= to < in the for loop condition. Multiple solutions work!', 'Learn about array bounds, loop conditions, and off-by-one errors in C++.', 'Using <= instead of < in loop conditions, not understanding zero-indexing.', 'Remember: array[0] to array[size-1] are valid. array[size] is out of bounds!', 12, 25, '[1, 2, 3, 4, 5]', '15', 'Basic positive numbers', 1, '[10, -5, 20]', '25', 'Mixed positive and negative', 1, '[]', '0', 'Empty vector edge case', 1, NULL, NULL, NULL, 1, NULL, NULL, NULL, 1, '[0, 0, 0]', '0', 'Hidden validation test', '[-10, 10, -5, 5]', '0', 'Hidden edge case', 'exact', 0.000001, 2025-07-04 17:28:33.474597, NULL, true, 0, 0.00, 0.00);

-- CPP_INTERMEDIATE CHALLENGES
-- 3 challenges

INSERT INTO cpp_intermediate (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts, hint_4, prerequisites, alternative_approaches, hidden_test_3_input, hidden_test_3_expected, hidden_test_3_description) VALUES (31, 'Fix the Factorial Function', 'Debug a recursive factorial function that has an incorrect base case.', 'You are given a recursive factorial function that should calculate n! (n factorial). However, the function has a bug in the base case that causes incorrect results. Find and fix the bug to make the factorial calculation work correctly.', '#include <iostream>
using namespace std;

long long factorial(int n) {
    if (n <= 1) {  // BUG: Should be n <= 0, not n <= 1
        return n;  // BUG: Should return 1, not n
    }
    
    return n * factorial(n - 1);
}', '#include <iostream>
using namespace std;

long long factorial(int n) {
    if (n <= 0) {  // FIXED: Correct base case
        return 1;  // FIXED: Return 1, not n
    }
    
    return n * factorial(n - 1);
}', 'The solution fixes the identified bugs in the function logic.', 'Look carefully at the initialization values and loop conditions.', 'Pay attention to the return statements and their logic.', 'Test with edge cases like empty inputs or single elements.', 'Students will learn to debug functions and understand common programming errors.', 'Common mistakes include off-by-one errors, incorrect return values, and wrong loop conditions.', 'Always trace through your code step by step with sample inputs.', 18, 35, '5', '120', 'Basic test case', 1, '0', '1', 'Second test case', 1, '1', '1', 'Edge case test', 1, '4', '24', 'Fourth test case', 1, '3', '6', 'Fifth test case', 1, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden edge case', 'exact', 0.000001, 2025-07-05 15:15:53.064590, NULL, true, 0, 0.00, 0.00, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO cpp_intermediate (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts, hint_4, prerequisites, alternative_approaches, hidden_test_3_input, hidden_test_3_expected, hidden_test_3_description) VALUES (32, 'Fix the String Reversal Function', 'Debug a function that reverses a string using two pointers but has index errors.', 'You are given a function that should reverse a string in-place using two pointers. However, the function has bugs in the pointer logic that cause incorrect results. Find and fix the bugs to make the string reversal work correctly.', '#include <string>
#include <iostream>
using namespace std;

void reverseString(string& s) {
    int left = 0;
    int right = s.length();  // BUG: Should be s.length() - 1
    
    while (left < right) {
        char temp = s[left];
        s[left] = s[right];
        s[right] = temp;
        
        left++;
        right++;  // BUG: Should be right--, not right++
    }
}

string testReverse(string input) {
    reverseString(input);
    return input;
}', '#include <string>
#include <iostream>
using namespace std;

void reverseString(string& s) {
    int left = 0;
    int right = s.length() - 1;  // FIXED: Correct initialization
    
    while (left < right) {
        char temp = s[left];
        s[left] = s[right];
        s[right] = temp;
        
        left++;
        right--;  // FIXED: Decrement right pointer
    }
}

string testReverse(string input) {
    reverseString(input);
    return input;
}', 'The solution fixes the identified bugs in the function logic.', 'Look carefully at the initialization values and loop conditions.', 'Pay attention to the return statements and their logic.', 'Test with edge cases like empty inputs or single elements.', 'Students will learn to debug functions and understand common programming errors.', 'Common mistakes include off-by-one errors, incorrect return values, and wrong loop conditions.', 'Always trace through your code step by step with sample inputs.', 18, 35, '"hello"', '"olleh"', 'Basic test case', 1, '"abc"', '"cba"', 'Second test case', 1, '"a"', '"a"', 'Edge case test', 1, '"12345"', '"54321"', 'Fourth test case', 1, '""', '""', 'Fifth test case', 1, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden edge case', 'exact', 0.000001, 2025-07-05 15:15:53.206143, NULL, true, 0, 0.00, 0.00, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO cpp_intermediate (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts, hint_4, prerequisites, alternative_approaches, hidden_test_3_input, hidden_test_3_expected, hidden_test_3_description) VALUES (30, 'Fix the Array Search Function', 'Debug a binary search function that has an off-by-one error causing incorrect results.', 'You are given a function that should find the index of element 5 in a sorted array. However, the function has a bug that causes it to return incorrect results or cause runtime errors. Find and fix the bug to make the search work correctly.', '#include <vector>
#include <iostream>
using namespace std;

int findElement(vector<int>& arr) {
    // Find the element 5 in the sorted array
    int left = 0;
    int right = arr.size();  // BUG: Should be arr.size() - 1
    int target = 5;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] == target) {
            return mid;
        }
        else if (arr[mid] < target) {
            left = mid + 1;
        }
        else {
            right = mid - 1;
        }
    }
    
    return -1;
}', '#include <vector>
#include <iostream>
using namespace std;

int findElement(vector<int>& arr) {
    // Find the element 5 in the sorted array
    int left = 0;
    int right = arr.size() - 1;  // FIXED: Correct initialization
    int target = 5;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] == target) {
            return mid;
        }
        else if (arr[mid] < target) {
            left = mid + 1;
        }
        else {
            right = mid - 1;
        }
    }
    
    return -1;
}', 'The solution fixes the identified bugs in the function logic.', 'Look carefully at the initialization values and loop conditions.', 'Pay attention to the return statements and their logic.', 'Test with edge cases like empty inputs or single elements.', 'Students will learn to debug functions and understand common programming errors.', 'Common mistakes include off-by-one errors, incorrect return values, and wrong loop conditions.', 'Always trace through your code step by step with sample inputs.', 18, 35, '[1, 3, 5, 7, 9]', '2', 'Basic test case', 1, '[2, 4, 6, 8, 10]', '-1', 'Second test case', 1, '[1, 2, 3, 4, 5]', '4', 'Edge case test', 1, '[5, 10, 15, 20]', '0', 'Fourth test case', 1, '[1, 2, 3, 4]', '-1', 'Fifth test case', 1, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden edge case', 'exact', 0.000001, 2025-07-05 15:15:52.943773, NULL, true, 0, 0.00, 0.00, NULL, NULL, NULL, NULL, NULL, NULL);

-- JAVA_BASIC CHALLENGES
-- 1 challenges

INSERT INTO java_basic (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (1, 'Fix the Minimum Finder', 'The findMinimum function has a bug with wrong initialization. Fix the bug so it correctly finds the minimum value in the array.', 'This function should find the minimum value in an array, but it incorrectly initializes min to 0, which fails for arrays containing only negative numbers.', 'public class ArrayProcessor {
    public static int findMinimum(int[] numbers) {
        int min = 0; // Bug: Wrong initialization for negative arrays!
        for (int i = 0; i < numbers.length; i++) {
            if (numbers[i] < min) {
                min = numbers[i];
            }
        }
        return min;
    }
}', 'public class ArrayProcessor {
    public static int findMinimum(int[] numbers) {
        if (numbers.length == 0) return 0; // Handle empty array
        int min = numbers[0]; // Fix: Initialize with first element
        for (int i = 1; i < numbers.length; i++) {
            if (numbers[i] < min) {
                min = numbers[i];
            }
        }
        return min;
    }
    
    public static void main(String[] args) {
        System.out.println("Function ready for testing");
    }
}', 'Initialize min with the first element instead of 0. Handle empty arrays appropriately.', 'Starting with min = 0 fails for negative-only arrays. Think about better initialization!', 'Try initializing min with the first element of the array instead of 0!', 'What if you set min = numbers[0] and start the loop from index 1?', 'Learn proper variable initialization and edge case handling in Java.', 'Using 0 as initial value for min, not handling empty arrays.', 'Initialize with the first element, or use Java 8 streams for alternative approaches.', 10, 20, '[5, -2, 8, -10, 3]', '-10', 'Mixed positive and negative numbers', 1, '[-1, -5, -3]', '-5', 'All negative numbers', 1, '[100]', '100', 'Single element', 1, NULL, NULL, NULL, 1, NULL, NULL, NULL, 1, '[0, -1, 1]', '-1', 'Hidden validation test', '[-100, -200]', '-200', 'Hidden edge case', 'exact', 0.000001, 2025-07-04 17:28:33.343035, NULL, true, 0, 0.00, 0.00);

-- JAVASCRIPT_BASIC CHALLENGES
-- 1 challenges

INSERT INTO javascript_basic (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts) VALUES (1, 'Fix the Max Finder', 'A function to find maximum values fails with negative numbers. Fix it your way!', 'Fix the findMax function that won''t work correctly for arrays containing only negative numbers. Any solution that passes the test cases is valid.', 'function findMax(numbers) {
    let max = numbers[0];
    for (let i = 1; i < numbers.length; i++) {
        if (numbers[i] > max) {
            max = numbers[i];
        }
    }
    // Bug: What if array is empty or contains only negative numbers?
    return max;
}', 'function findMax(arr) {
    if (arr.length === 0) return undefined;
    let max = arr[0];  // Initialize with first element
    for (let i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}', 'This is one approach. You could also use Math.max(...arr), a reduce function, or other methods.', 'Starting with max = 0 won''t work for arrays with only negative numbers!', 'Try initializing max with the first element of the array, or use built-in JavaScript methods.', 'Handle empty arrays appropriately - they should return undefined.', 'Learn about proper variable initialization and different approaches to finding maximum values.', 'Assuming 0 is a good initial value. This fails when all numbers are negative.', 'Multiple solutions exist: Math.max, reduce, traditional loops, etc. Pick what feels natural to you!', 10, 15, '[3, 7, 2, 9, 1]', '9', 'Standard case with positive numbers', 1, '[-5, -2, -8, -1]', '-1', 'Edge case: all negative numbers', 2, '[]', 'undefined', 'Edge case: empty array', 1, NULL, NULL, NULL, 1, NULL, NULL, NULL, 1, '[0]', '0', 'Hidden validation test', '[-10, -20, -5]', '-5', 'Hidden edge case', 'exact', 0.000001, 2025-07-04 16:47:21.799786, NULL, true, 0, 0.00, 0.00);

-- JAVASCRIPT_INTERMEDIATE CHALLENGES
-- 1 challenges

INSERT INTO javascript_intermediate (challenge_id, title, description, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, common_mistakes, tips, max_score, time_limit_minutes, test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight, test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight, test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight, test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight, test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight, hidden_test_1_input, hidden_test_1_expected, hidden_test_1_description, hidden_test_2_input, hidden_test_2_expected, hidden_test_2_description, output_comparison_type, tolerance_for_float, created_at, created_by, is_active, completion_count, success_rate, avg_attempts, hint_4, prerequisites, alternative_approaches, hidden_test_3_input, hidden_test_3_expected, hidden_test_3_description) VALUES (29, 'Async Promise Chain Bug', 'Fix the bug in this Promise chain that causes incorrect async behavior.', 'This function should fetch user data, then fetch their posts, and return a combined result. However, there''s a bug in the Promise chain that causes race conditions and incorrect results.', 'async function getUserWithPosts(userId) {
    const userData = fetch(`/api/users/${userId}`)
        .then(response => response.json());
    
    const userPosts = fetch(`/api/users/${userId}/posts`)  // BUG: Not waiting for userData
        .then(response => response.json());
    
    // BUG: Promise.all won''t work correctly here
    return Promise.all([userData, userPosts])
        .then(([user, posts]) => {
            return {
                user: user,
                posts: posts,
                totalPosts: posts.length
            };
        });
}

// Test
console.log(getUserWithPosts(123));', 'async function getUserWithPosts(userId) {
    const userData = await fetch(`/api/users/${userId}`)
        .then(response => response.json());
    
    const userPosts = await fetch(`/api/users/${userId}/posts`)
        .then(response => response.json());
    
    return {
        user: userData,
        posts: userPosts,
        totalPosts: userPosts.length
    };
}

// Test  
console.log(await getUserWithPosts(123));', 'The bug was in not properly awaiting the async operations. The original code started both requests simultaneously but didn''t handle the async nature correctly.', 'Look at how async/await and Promises are being mixed. Is this the best approach?', 'Consider whether both API calls should happen simultaneously or sequentially.', 'Think about when each Promise resolves and what data is available when.', 'Students will learn debugging techniques and improve their javascript programming skills.', 'Common mistakes include off-by-one errors, uninitialized variables, and incorrect conditional logic.', 'Always test your code with different inputs, especially edge cases and boundary values.', 15, 25, '123', '{user: {id: 123, name: ''John''}, posts: [{id: 1, title: ''Hello''}], totalPosts: 1}', 'Valid user with posts', 2, '456', '{user: {id: 456, name: ''Jane''}, posts: [], totalPosts: 0}', 'User with no posts', 2, '999', 'null', 'Non-existent user', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'Hidden validation test', NULL, NULL, 'Hidden edge case', 'exact', 0.000001, 2025-07-05 14:01:34.438281, NULL, true, 0, 0.00, 0.00, NULL, NULL, NULL, NULL, NULL, NULL);
