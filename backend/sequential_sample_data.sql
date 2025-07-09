-- Independent Sequential Sample data for BugYou challenges
-- Each table now has its own independent sequential IDs starting from 1

-- Python Basic Challenges (IDs: 1, 2)
INSERT INTO python_basic (
    title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected
) VALUES
('Find Maximum Number', 
'Write a function that finds the maximum number in a list. The function should handle edge cases like empty lists and lists with negative numbers.', 
'def find_max(numbers):
    max_num = 0
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num', 
'def find_max(numbers):
    if not numbers:
        return None
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num', 
'The bug is in the initialization of max_num. Starting with 0 fails for lists with only negative numbers. We should initialize with the first element of the list.', 
'What happens when all numbers in the list are negative?', 
'Try initializing max_num with the first element of the list instead of 0.', 
'Consider what happens with an empty list - should we return None or 0?', 
'Students will learn about proper variable initialization and edge case handling.', 
'[1, 2, 3, 4, 5]', '5', '[-1, -2, -3]', '-1', '[]', 'None'),

('Count Even Numbers', 
'Write a function that counts the number of even numbers in a list.', 
'def count_even(numbers):
    count = 0
    for i in range(len(numbers)):
        if numbers[i] % 2 == 0:
            count += 1
        return count', 
'def count_even(numbers):
    count = 0
    for i in range(len(numbers)):
        if numbers[i] % 2 == 0:
            count += 1
    return count', 
'The bug is in the indentation of the return statement. It should be outside the for loop, not inside it.', 
'Look at the indentation of the return statement.', 
'The return statement should be at the same level as the for loop, not inside it.', 
'Check if the return statement is properly aligned.', 
'Students will learn about proper indentation and loop control flow.', 
'[1, 2, 3, 4, 5, 6]', '3', '[2, 4, 6, 8]', '4', '[1, 3, 5]', '0');

-- JavaScript Basic Challenges (ID: 1)
INSERT INTO javascript_basic (
    title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected
) VALUES
('Calculate Sum', 
'Write a function that calculates the sum of all numbers in an array. Handle edge cases properly.', 
'function calculateSum(arr) {
    let sum = 0;
    for (let i = 0; i <= arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}', 
'function calculateSum(arr) {
    if (!arr || arr.length === 0) {
        return 0;
    }
    let sum = 0;
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}', 
'The bug is in the loop condition. Using <= instead of < causes an off-by-one error, accessing an undefined element.', 
'What happens when i equals arr.length?', 
'Arrays are zero-indexed. If length is 5, valid indices are 0-4, not 0-5.', 
'Change <= to < in the for loop condition.', 
'Students will learn about off-by-one errors and proper array indexing.', 
'[1, 2, 3, 4, 5]', '15', '[10, 20, 30]', '60', '[]', '0');

-- Java Basic Challenges (ID: 1)
INSERT INTO java_basic (
    title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected
) VALUES
('Find Minimum', 
'Write a function that finds the minimum number in an array. Handle edge cases properly.', 
'public static int findMin(int[] numbers) {
    int min = 0;
    for (int i = 0; i < numbers.length; i++) {
        if (numbers[i] < min) {
            min = numbers[i];
        }
    }
    return min;
}', 
'public static int findMin(int[] numbers) {
    if (numbers == null || numbers.length == 0) {
        throw new IllegalArgumentException("Array cannot be null or empty");
    }
    int min = numbers[0];
    for (int i = 1; i < numbers.length; i++) {
        if (numbers[i] < min) {
            min = numbers[i];
        }
    }
    return min;
}', 
'The bug is in the initialization of min. Starting with 0 fails for arrays with only positive numbers. We should initialize with the first element.', 
'What happens when all numbers in the array are positive?', 
'Try initializing min with the first element of the array instead of 0.', 
'Start the loop from index 1 since we already have the first element as min.', 
'Students will learn about proper variable initialization and array handling.', 
'{1, 2, 3, 4, 5}', '1', '{10, 5, 8, 2}', '2', '{7, 7, 7}', '7');

-- C++ Basic Challenges (ID: 1)
INSERT INTO cpp_basic (
    title, problem_statement, buggy_code, reference_solution, 
    solution_explanation, hint_1, hint_2, hint_3, learning_objectives, 
    test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, 
    test_case_3_input, test_case_3_expected
) VALUES
('Count Elements', 
'Write a function that counts the number of elements in a vector. Handle edge cases properly.', 
'int countElements(std::vector<int>& numbers) {
    int count = 0;
    for (int i = 0; i <= numbers.size(); i++) {
        count++;
    }
    return count;
}', 
'int countElements(std::vector<int>& numbers) {
    return numbers.size();
}', 
'The bug is in the loop condition. Using <= instead of < causes an off-by-one error. Also, we can simply return numbers.size() instead of counting manually.', 
'What happens when i equals numbers.size()?', 
'Vectors are zero-indexed. If size is 5, valid indices are 0-4, not 0-5.', 
'Why count manually when you can use the size() method?', 
'Students will learn about off-by-one errors and STL usage.', 
'{1, 2, 3, 4, 5}', '5', '{10, 20}', '2', '{}', '0'); 