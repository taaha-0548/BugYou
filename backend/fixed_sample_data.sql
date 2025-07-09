-- Fixed Sample data for BugYou challenges
-- Insert sample challenges into each table with proper column count

-- Python Basic Challenges
INSERT INTO python_basic (
    challenge_id, title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected,
    test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected, created_by
) VALUES
(1, 'Find Maximum Number', 'Write a function that finds the maximum number in a list. The function should handle edge cases like empty lists and lists with negative numbers.', 'def find_max(numbers):\n    max_num = 0\n    for num in numbers:\n        if num > max_num:\n            max_num = num\n    return max_num', 'def find_max(numbers):\n    if not numbers:\n        return None\n    max_num = numbers[0]\n    for num in numbers:\n        if num > max_num:\n            max_num = num\n    return max_num', 'The bug is in the initialization of max_num. Starting with 0 fails for lists with only negative numbers. We should initialize with the first element of the list.', 'What happens when all numbers in the list are negative?', 'Try initializing max_num with the first element of the list instead of 0.', 'Consider what happens with an empty list - should we return None or 0?', 'Students will learn about proper variable initialization and edge case handling.', 10, '[1, 2, 3, 4, 5]', '5', '[-1, -2, -3]', '-1', '[]', 'None', NULL, NULL, NULL, NULL, '[10, 5, 8]', '10', '[-10, -5]', '-5', 1),
(2, 'Count Even Numbers', 'Write a function that counts the number of even numbers in a list.', 'def count_even(numbers):\n    count = 0\n    for i in range(len(numbers)):\n        if numbers[i] % 2 == 0:\n            count += 1\n        return count', 'def count_even(numbers):\n    count = 0\n    for i in range(len(numbers)):\n        if numbers[i] % 2 == 0:\n            count += 1\n    return count', 'The bug is in the indentation of the return statement. It should be outside the for loop, not inside it.', 'Look at the indentation of the return statement.', 'The return statement should be at the same level as the for loop, not inside it.', 'Check if the return statement is properly aligned.', 'Students will learn about proper indentation and loop control flow.', 10, '[1, 2, 3, 4, 5, 6]', '3', '[2, 4, 6, 8]', '4', '[1, 3, 5]', '0', NULL, NULL, NULL, NULL, '[7, 8, 9, 10]', '2', '[11, 12, 13, 14, 15]', '2', 1);

-- Python Intermediate Challenges
INSERT INTO python_intermediate (
    challenge_id, title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected,
    test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected, created_by
) VALUES
(1, 'Remove Duplicates', 'Write a function that removes duplicate elements from a list while preserving the order.', 'def remove_duplicates(lst):\n    result = []\n    for item in lst:\n        if item not in result:\n            result.append(item)\n    return result', 'def remove_duplicates(lst):\n    if not lst:\n        return []\n    result = []\n    for item in lst:\n        if item not in result:\n            result.append(item)\n    return result', 'The function is mostly correct, but it should handle the case of an empty list explicitly.', 'What happens when the input list is empty?', 'Add a check for empty list at the beginning.', 'Consider edge cases like None or empty list.', 'Students will learn about edge case handling and list operations.', 10, '[1, 2, 2, 3, 4, 4, 5]', '[1, 2, 3, 4, 5]', '[1, 1, 1]', '[1]', '[]', '[]', NULL, NULL, NULL, NULL, '[1, 2, 1, 3, 2]', '[1, 2, 3]', '[5, 5, 5, 5]', '[5]', 1);

-- JavaScript Basic Challenges
INSERT INTO javascript_basic (
    challenge_id, title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected,
    test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected, created_by
) VALUES
(1, 'Calculate Sum', 'Write a function that calculates the sum of all numbers in an array. Handle edge cases properly.', 'function calculateSum(arr) {\n    let sum = 0;\n    for (let i = 0; i <= arr.length; i++) {\n        sum += arr[i];\n    }\n    return sum;\n}', 'function calculateSum(arr) {\n    if (!arr || arr.length === 0) {\n        return 0;\n    }\n    let sum = 0;\n    for (let i = 0; i < arr.length; i++) {\n        sum += arr[i];\n    }\n    return sum;\n}', 'The bug is in the loop condition. Using <= instead of < causes an off-by-one error, accessing an undefined element.', 'What happens when i equals arr.length?', 'Arrays are zero-indexed. If length is 5, valid indices are 0-4, not 0-5.', 'Change <= to < in the for loop condition.', 10, '[1, 2, 3, 4, 5]', '15', '[10, 20, 30]', '60', '[]', '0', NULL, NULL, NULL, NULL, '[5, 5, 5]', '15', '[100]', '100', 1);

-- Java Basic Challenges
INSERT INTO java_basic (
    challenge_id, title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected,
    test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected, created_by
) VALUES
(1, 'Find Minimum', 'Write a function that finds the minimum number in an array. Handle edge cases properly.', 'public static int findMin(int[] numbers) {\n    int min = 0;\n    for (int i = 0; i < numbers.length; i++) {\n        if (numbers[i] < min) {\n            min = numbers[i];\n        }\n    }\n    return min;\n}', 'public static int findMin(int[] numbers) {\n    if (numbers == null || numbers.length == 0) {\n        throw new IllegalArgumentException("Array cannot be null or empty");\n    }\n    int min = numbers[0];\n    for (int i = 1; i < numbers.length; i++) {\n        if (numbers[i] < min) {\n            min = numbers[i];\n        }\n    }\n    return min;\n}', 'The bug is in the initialization of min. Starting with 0 fails for arrays with only positive numbers. We should initialize with the first element.', 'What happens when all numbers in the array are positive?', 'Try initializing min with the first element of the array instead of 0.', 'Start the loop from index 1 since we already have the first element as min.', 10, '{1, 2, 3, 4, 5}', '1', '{10, 5, 8, 2}', '2', '{7, 7, 7}', '7', NULL, NULL, NULL, NULL, '{100, 50, 75}', '50', '{9, 8, 7}', '7', 1);

-- C++ Basic Challenges
INSERT INTO cpp_basic (
    challenge_id, title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected,
    test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected, created_by
) VALUES
(1, 'Count Elements', 'Write a function that counts the number of elements in a vector. Handle edge cases properly.', '#include <vector>\n#include <iostream>\n\nint countElements(std::vector<int>& numbers) {\n    int count = 0;\n    for (int i = 0; i <= numbers.size(); i++) {\n        count++;\n    }\n    return count;\n}', '#include <vector>\n#include <iostream>\n\nint countElements(std::vector<int>& numbers) {\n    return numbers.size();\n}', 'The bug is in the loop condition. Using <= instead of < causes an off-by-one error. Also, we can simply return numbers.size() instead of counting manually.', 'What happens when i equals numbers.size()?', 'Vectors are zero-indexed. If size is 5, valid indices are 0-4, not 0-5.', 'Why count manually when you can use the size() method?', 10, '{1, 2, 3, 4, 5}', '5', '{10, 20}', '2', '{}', '0', NULL, NULL, NULL, NULL, '{100}', '1', '{1, 2, 3}', '3', 1); 