-- Sample data for BugYou challenges
-- Each table now has independent sequential IDs starting from 1

-- Insert a default user for created_by reference
INSERT INTO users (username) VALUES ('system');

-- Python Basic Challenges
INSERT INTO python_basic (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Find Maximum Number', 'Write a function that finds the maximum number in a list. The function should handle edge cases like empty lists and lists with negative numbers.', 'def find_max(numbers):
    max_num = 0
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num', 'def find_max(numbers):
    if not numbers:
        return None
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num', 'The bug is in the initialization of max_num. Starting with 0 fails for lists with only negative numbers. We should initialize with the first element of the list.', 'What happens when all numbers in the list are negative?', 'Try initializing max_num with the first element of the list instead of 0.', 'Consider what happens with an empty list - should we return None or 0?', 'Students will learn about proper variable initialization and edge case handling.', 10, '[1, 2, 3, 4, 5]', '5', '[-1, -2, -3]', '-1', '[]', 'None', '[10, 15, 20]', '20', '[100]', '100', '[50, 40, 30]', '50', '[-5, -10, -15]', '-5', 1, 0.0, 0.0),
('Count Even Numbers', 'Write a function that counts the number of even numbers in a list.', 'def count_even(numbers):
    count = 0
    for i in range(len(numbers)):
        if numbers[i] % 2 == 0:
            count += 1
        return count', 'def count_even(numbers):
    count = 0
    for i in range(len(numbers)):
        if numbers[i] % 2 == 0:
            count += 1
    return count', 'The bug is in the indentation of the return statement. It should be outside the for loop, not inside it.', 'Look at the indentation of the return statement.', 'The return statement should be at the same level as the for loop, not inside it.', 'Check if the return statement is properly aligned.', 'Students will learn about proper indentation and loop control flow.', 10, '[1, 2, 3, 4, 5, 6]', '3', '[2, 4, 6, 8]', '4', '[1, 3, 5]', '0', '[7, 8, 9, 10]', '2', '[11, 12, 13, 14, 15, 16]', '3', '[2, 4, 6, 8, 10, 12]', '6', '[1, 3, 5, 7, 9, 11]', '0', 1, 0.0, 0.0);

-- Python Intermediate Challenges
INSERT INTO python_intermediate (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Remove Duplicates', 'Write a function that removes duplicate elements from a list while preserving the order.', 'def remove_duplicates(lst):
    result = []
    for item in lst:
        if item not in result:
            result.append(item)
    return result', 'def remove_duplicates(lst):
    if not lst:
        return []
    result = []
    for item in lst:
        if item not in result:
            result.append(item)
    return result', 'The function is mostly correct, but it should handle the case of an empty list explicitly.', 'What happens when the input list is empty?', 'Add a check for empty list at the beginning.', 'Consider edge cases like None or empty list.', 'Students will learn about edge case handling and list operations.', 10, '[1, 2, 2, 3, 4, 4, 5]', '[1, 2, 3, 4, 5]', '[1, 1, 1]', '[1]', '[]', '[]', '[5, 5, 5, 5]', '[5]', '[1, 2, 1, 3, 2, 4]', '[1, 2, 3, 4]', '[7, 8, 7, 9, 8, 10]', '[7, 8, 9, 10]', '[6, 6, 6]', '[6]', 1, 0.0, 0.0);

-- Python Advanced Challenges
INSERT INTO python_advanced (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Binary Search', 'Implement binary search to find a target number in a sorted array.', 'def binary_search(arr, target):
    left, right = 0, len(arr)
    while left < right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid
        else:
            right = mid
    return -1', 'def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1', 'The bugs are: 1) right should be len(arr) - 1, 2) loop condition should be <=, 3) left should be mid + 1, 4) right should be mid - 1.', 'Check the initial value of right.', 'Look at the loop condition and update logic.', 'Consider how the search space should be reduced.', 10, '[1, 2, 3, 4, 5]', '2', '[1, 3, 5, 7, 9]', '4', '[1, 2, 3, 4, 5]', '-1', '[2, 4, 6, 8, 10]', '2', '[1, 3, 5, 7, 9, 11]', '5', '[10, 20, 30, 40, 50]', '2', '[5, 15, 25, 35, 45]', '-1', 1, 0.0, 0.0);

-- JavaScript Basic Challenges
INSERT INTO javascript_basic (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Calculate Sum', 'Write a function that calculates the sum of all numbers in an array. Handle edge cases properly.', 'function calculateSum(arr) {
    let sum = 0;
    for (let i = 0; i <= arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}', 'function calculateSum(arr) {
    if (!arr || arr.length === 0) {
        return 0;
    }
    let sum = 0;
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}', 'The bug is in the loop condition. Using <= instead of < causes an off-by-one error, accessing an undefined element.', 'What happens when i equals arr.length?', 'Arrays are zero-indexed. If length is 5, valid indices are 0-4, not 0-5.', 'Change <= to < in the for loop condition.', 10, '[1, 2, 3, 4, 5]', '15', '[10, 20, 30]', '60', '[]', '0', '[7, 8, 9]', '24', '[100]', '100', '[5, 10, 15, 20]', '50', '[25, 25, 25, 25]', '100', 1, 0.0, 0.0);

-- JavaScript Intermediate Challenges
INSERT INTO javascript_intermediate (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Reverse String', 'Write a function that reverses a string without using the built-in reverse method.', 'function reverseString(str) {
    let reversed = "";
    for (let i = 0; i < str.length; i++) {
        reversed = str[i] + reversed;
    }
    return reversed;
}', 'function reverseString(str) {
    if (!str) {
        return "";
    }
    let reversed = "";
    for (let i = 0; i < str.length; i++) {
        reversed = str[i] + reversed;
    }
    return reversed;
}', 'The function should handle null or undefined input.', 'What happens when the input is null or undefined?', 'Add a check for null/undefined input.', 'Consider edge cases like empty string.', 10, '"hello"', '"olleh"', '"world"', '"dlrow"', '""', '""', '"test"', '"tset"', '"a"', '"a"', '"programming"', '"gnimmargorpP', '"javascript"', '"tpircsavaJ"', 1, 0.0, 0.0);

-- JavaScript Advanced Challenges
INSERT INTO javascript_advanced (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Find Longest Substring', 'Write a function that finds the length of the longest substring without repeating characters.', 'function lengthOfLongestSubstring(s) {
    let maxLength = 0;
    let start = 0;
    let charMap = {};
    
    for (let i = 0; i < s.length; i++) {
        if (charMap[s[i]] >= start) {
            start = charMap[s[i]] + 1;
        }
        charMap[s[i]] = i;
        maxLength = Math.max(maxLength, i - start + 1);
    }
    return maxLength;
}', 'function lengthOfLongestSubstring(s) {
    if (!s) {
        return 0;
    }
    let maxLength = 0;
    let start = 0;
    let charMap = {};
    
    for (let i = 0; i < s.length; i++) {
        if (charMap[s[i]] >= start) {
            start = charMap[s[i]] + 1;
        }
        charMap[s[i]] = i;
        maxLength = Math.max(maxLength, i - start + 1);
    }
    return maxLength;
}', 'The function should handle null or undefined input.', 'What happens when the input is null or undefined?', 'Add a check for null/undefined input.', 'Consider edge cases like empty string.', 10, '"abcabcbb"', '3', '"bbbbb"', '1', '""', '0', '"pwwkew"', '3', '"dvdf"', '3', '"abcdef"', '6', '"aabbcc"', '2', 1, 0.0, 0.0);

-- Java Basic Challenges
INSERT INTO java_basic (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Find Minimum', 'Write a function that finds the minimum number in an array. Handle edge cases properly.', 'public static int findMin(int[] numbers) {
    int min = 0;
    for (int i = 0; i < numbers.length; i++) {
        if (numbers[i] < min) {
            min = numbers[i];
        }
    }
    return min;
}', 'public static int findMin(int[] numbers) {
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
}', 'The bug is in the initialization of min. Starting with 0 fails for arrays with only positive numbers. We should initialize with the first element.', 'What happens when all numbers in the array are positive?', 'Try initializing min with the first element of the array instead of 0.', 'Start the loop from index 1 since we already have the first element as min.', 10, '{1, 2, 3, 4, 5}', '1', '{10, 5, 8, 2}', '2', '{7, 7, 7}', '7', '{15, 12, 18, 9}', '9', '{100}', '100', '{50, 60, 40, 70}', '40', '{25, 35, 20, 45}', '20', 1, 0.0, 0.0);

-- Java Intermediate Challenges
INSERT INTO java_intermediate (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Check Prime Number', 'Write a function that checks if a number is prime.', 'public static boolean isPrime(int n) {
    if (n <= 1) {
        return false;
    }
    for (int i = 2; i < n; i++) {
        if (n % i == 0) {
            return false;
        }
    }
    return true;
}', 'public static boolean isPrime(int n) {
    if (n <= 1) {
        return false;
    }
    if (n == 2) {
        return true;
    }
    if (n % 2 == 0) {
        return false;
    }
    for (int i = 3; i <= Math.sqrt(n); i += 2) {
        if (n % i == 0) {
            return false;
        }
    }
    return true;
}', 'The function can be optimized by checking only up to square root and skipping even numbers.', 'Do we need to check all numbers up to n?', 'We only need to check up to the square root of n.', 'We can skip even numbers after checking 2.', 10, '7', 'true', '4', 'false', '1', 'false', '11', 'true', '13', 'true', '17', 'true', '15', 'false', 1, 0.0, 0.0);

-- Java Advanced Challenges
INSERT INTO java_advanced (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Merge Sort', 'Implement merge sort algorithm to sort an array.', 'public static void mergeSort(int[] arr) {
    if (arr.length <= 1) {
        return;
    }
    int mid = arr.length / 2;
    int[] left = new int[mid];
    int[] right = new int[arr.length - mid];
    
    for (int i = 0; i < mid; i++) {
        left[i] = arr[i];
    }
    for (int i = mid; i < arr.length; i++) {
        right[i - mid] = arr[i];
    }
    
    mergeSort(left);
    mergeSort(right);
    merge(arr, left, right);
}', 'public static void mergeSort(int[] arr) {
    if (arr == null || arr.length <= 1) {
        return;
    }
    int mid = arr.length / 2;
    int[] left = new int[mid];
    int[] right = new int[arr.length - mid];
    
    for (int i = 0; i < mid; i++) {
        left[i] = arr[i];
    }
    for (int i = mid; i < arr.length; i++) {
        right[i - mid] = arr[i];
    }
    
    mergeSort(left);
    mergeSort(right);
    merge(arr, left, right);
}', 'The function should handle null input.', 'What happens when the input array is null?', 'Add a check for null input.', 'Consider edge cases like null or empty array.', 10, '{5, 2, 8, 1, 9}', '{1, 2, 5, 8, 9}', '{3, 1, 4, 1, 5}', '{1, 1, 3, 4, 5}', '{}', '{}', '{7, 3, 9, 1}', '{1, 3, 7, 9}', '{6}', '{6}', '{10, 5, 15, 3, 12}', '{3, 5, 10, 12, 15}', '{8, 4, 2, 6}', '{2, 4, 6, 8}', 1, 0.0, 0.0);

-- C++ Basic Challenges
INSERT INTO cpp_basic (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Count Elements', 'Write a function that counts the number of elements in a vector. Handle edge cases properly.', 'int countElements(std::vector<int>& numbers) {
    int count = 0;
    for (int i = 0; i <= numbers.size(); i++) {
        count++;
    }
    return count;
}', 'int countElements(std::vector<int>& numbers) {
    return numbers.size();
}', 'The bug is in the loop condition. Using <= instead of < causes an off-by-one error. Also, we can simply return numbers.size() instead of counting manually.', 'What happens when i equals numbers.size()?', 'Vectors are zero-indexed. If size is 5, valid indices are 0-4, not 0-5.', 'Why count manually when you can use the size() method?', 10, '{1, 2, 3, 4, 5}', '5', '{10, 20}', '2', '{}', '0', '{7, 8, 9, 10, 11, 12}', '6', '{100}', '1', '{15, 25, 35}', '3', '{50, 60, 70, 80}', '4', 1, 0.0, 0.0);

-- C++ Intermediate Challenges
INSERT INTO cpp_intermediate (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Remove Duplicates', 'Write a function that removes duplicate elements from a vector.', 'std::vector<int> removeDuplicates(std::vector<int>& numbers) {
    std::vector<int> result;
    for (int i = 0; i < numbers.size(); i++) {
        bool found = false;
        for (int j = 0; j < result.size(); j++) {
            if (numbers[i] == result[j]) {
                found = true;
                break;
            }
        }
        if (!found) {
            result.push_back(numbers[i]);
        }
    }
    return result;
}', 'std::vector<int> removeDuplicates(std::vector<int>& numbers) {
    if (numbers.empty()) {
        return {};
    }
    std::vector<int> result;
    for (int i = 0; i < numbers.size(); i++) {
        if (std::find(result.begin(), result.end(), numbers[i]) == result.end()) {
            result.push_back(numbers[i]);
        }
    }
    return result;
}', 'The function can be optimized using std::find instead of manual loop.', 'Is there a standard library function to find an element?', 'Use std::find to check if an element exists in the result vector.', 'Consider using STL algorithms for better performance.', 10, '{1, 2, 2, 3, 4, 4, 5}', '{1, 2, 3, 4, 5}', '{1, 1, 1}', '{1}', '{}', '{}', '{5, 5, 5, 5}', '{5}', '{7, 8, 7, 9, 8}', '{7, 8, 9}', '{10, 20, 10, 30, 20}', '{10, 20, 30}', '{6, 6, 6}', '{6}', 1, 0.0, 0.0);

-- C++ Advanced Challenges
INSERT INTO cpp_advanced (title, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3, learning_objectives, max_score, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected, test_case_3_input, test_case_3_expected, test_case_4_input, test_case_4_expected, test_case_5_input, test_case_5_expected, hidden_test_1_input, hidden_test_1_expected, hidden_test_2_input, hidden_test_2_expected, created_by, success_rate, avg_attempts) VALUES
('Binary Search', 'Implement binary search to find a target number in a sorted vector.', 'int binarySearch(std::vector<int>& arr, int target) {
    int left = 0;
    int right = arr.size();
    while (left < right) {
        int mid = (left + right) / 2;
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid;
        } else {
            right = mid;
        }
    }
    return -1;
}', 'int binarySearch(std::vector<int>& arr, int target) {
    if (arr.empty()) {
        return -1;
    }
    int left = 0;
    int right = arr.size() - 1;
    while (left <= right) {
        int mid = (left + right) / 2;
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}', 'The bugs are: 1) right should be arr.size() - 1, 2) loop condition should be <=, 3) left should be mid + 1, 4) right should be mid - 1.', 'Check the initial value of right.', 'Look at the loop condition and update logic.', 'Consider how the search space should be reduced.', 10, '{1, 2, 3, 4, 5}', '2', '{1, 3, 5, 7, 9}', '4', '{1, 2, 3, 4, 5}', '-1', '{2, 4, 6, 8, 10}', '2', '{10, 20, 30}', '1', '{5, 15, 25, 35, 45}', '2', '{1, 11, 21, 31}', '-1', 1, 0.0, 0.0); 