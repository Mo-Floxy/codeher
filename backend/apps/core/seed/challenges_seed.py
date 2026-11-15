"""Sample coding challenges.

Each entry grades a single function named `solution`. Public cases are shown in
the instructions; hidden cases only ever run inside the sandbox and are never
serialised to the frontend.
"""

CHALLENGES = [
    {
        "title": "Reverse a String",
        "summary": "Take a word and send it back the other way.",
        "description": (
            "Write a function called `solution` that takes one string and returns it reversed.\n\n"
            "Do not change the characters, only their order. An empty string reversed is still "
            "an empty string."
        ),
        "difficulty": "beginner",
        "category": "javascript",
        "points": 15,
        "topics": ["strings", "loops"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(text) {\n  // return the characters of text in reverse order\n}\n",
            "python": "def solution(text):\n    # return the characters of text in reverse order\n",
        },
        "examples": [
            {"input": ["hello"], "output": "olleh"},
            {"input": ["CodeHer"], "output": "reHedoC"},
        ],
        "hints": [
            "In JavaScript, split into an array, reverse it, then join it back together.",
            "In Python, the slice text[::-1] walks the string backwards.",
        ],
        "tests": [
            {"name": "hello", "args": ["hello"], "expected": "olleh", "public": True},
            {"name": "CodeHer", "args": ["CodeHer"], "expected": "reHedoC", "public": True},
            {"name": "empty string", "args": [""], "expected": "", "public": False},
            {"name": "single character", "args": ["z"], "expected": "z", "public": False},
            {"name": "palindrome", "args": ["racecar"], "expected": "racecar", "public": False},
            {"name": "with spaces", "args": ["be you"], "expected": "uoy eb", "public": False},
        ],
    },
    {
        "title": "Sum an Array",
        "summary": "Add every number in a list.",
        "description": (
            "Write `solution` so it returns the total of all numbers in the array it receives.\n\n"
            "The array may be empty, and the numbers may be negative. An empty array sums to 0."
        ),
        "difficulty": "beginner",
        "category": "javascript",
        "points": 15,
        "topics": ["arrays", "accumulators"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(numbers) {\n  // return the sum of every number\n}\n",
            "python": "def solution(numbers):\n    # return the sum of every number\n",
        },
        "examples": [
            {"input": [[1, 2, 3, 4]], "output": 10},
            {"input": [[-2, 2]], "output": 0},
        ],
        "hints": ["JavaScript has numbers.reduce((total, n) => total + n, 0).", "Python has a built-in sum()."],
        "tests": [
            {"name": "1..4", "args": [[1, 2, 3, 4]], "expected": 10, "public": True},
            {"name": "negatives cancel", "args": [[-2, 2]], "expected": 0, "public": True},
            {"name": "empty array", "args": [[]], "expected": 0, "public": False},
            {"name": "one value", "args": [[42]], "expected": 42, "public": False},
            {"name": "all negative", "args": [[-1, -2, -3]], "expected": -6, "public": False},
        ],
    },
    {
        "title": "Largest Number",
        "summary": "Find the maximum without sorting.",
        "description": (
            "Write `solution` to return the largest number in the given array.\n\n"
            "The array always has at least one element, so you never need to handle empty input. "
            "Try to solve it with a single pass instead of sorting."
        ),
        "difficulty": "beginner",
        "category": "algorithms",
        "points": 15,
        "topics": ["arrays", "comparison"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(numbers) {\n  // return the largest number\n}\n",
            "python": "def solution(numbers):\n    # return the largest number\n",
        },
        "examples": [{"input": [[3, 1, 4, 1, 5]], "output": 5}, {"input": [[-7, -2]], "output": -2}],
        "hints": ["Start with the first element as your current best, then compare the rest."],
        "tests": [
            {"name": "mixed", "args": [[3, 1, 4, 1, 5]], "expected": 5, "public": True},
            {"name": "all negative", "args": [[-7, -2]], "expected": -2, "public": True},
            {"name": "single element", "args": [[9]], "expected": 9, "public": False},
            {"name": "max at the end", "args": [[1, 2, 3, 99]], "expected": 99, "public": False},
            {"name": "duplicates", "args": [[5, 5, 5]], "expected": 5, "public": False},
        ],
    },
    {
        "title": "Count the Vowels",
        "summary": "How many lowercase vowels are in this text?",
        "description": (
            "Write `solution` to count how many of the characters a, e, i, o, u appear in the "
            "input string.\n\n"
            "Counting is case sensitive: uppercase vowels do not count. Spaces and punctuation are "
            "ignored because they are not vowels."
        ),
        "difficulty": "beginner",
        "category": "python",
        "points": 20,
        "topics": ["strings", "counting"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(text) {\n  // count a, e, i, o, u\n}\n",
            "python": "def solution(text):\n    # count a, e, i, o, u\n",
        },
        "examples": [{"input": ["Mississippi"], "output": 4}, {"input": ["xyz"], "output": 0}],
        "hints": ["Loop over the characters and check membership in the string 'aeiou'."],
        "tests": [
            {"name": "Mississippi", "args": ["Mississippi"], "expected": 4, "public": True},
            {"name": "no vowels", "args": ["xyz"], "expected": 0, "public": True},
            {"name": "uppercase does not count", "args": ["AEIOU"], "expected": 0, "public": False},
            {"name": "empty string", "args": [""], "expected": 0, "public": False},
            {"name": "sentence", "args": ["she codes every day"], "expected": 6, "public": False},
        ],
    },
    {
        "title": "Running Total",
        "summary": "Turn a list into its cumulative sums.",
        "description": (
            "Write `solution` to return a new array where each element is the sum of everything up "
            "to and including that position.\n\n"
            "For [1, 2, 3, 4] the answer is [1, 3, 6, 10]. Never modify the input array."
        ),
        "difficulty": "beginner",
        "category": "data",
        "points": 20,
        "topics": ["arrays", "prefix sums"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(numbers) {\n  // return the running totals\n}\n",
            "python": "def solution(numbers):\n    # return the running totals\n",
        },
        "examples": [{"input": [[1, 2, 3, 4]], "output": [1, 3, 6, 10]}, {"input": [[5]], "output": [5]}],
        "hints": ["Keep a `total` variable outside the loop and push it after adding each number."],
        "tests": [
            {"name": "1..4", "args": [[1, 2, 3, 4]], "expected": [1, 3, 6, 10], "public": True},
            {"name": "single", "args": [[5]], "expected": [5], "public": True},
            {"name": "empty", "args": [[]], "expected": [], "public": False},
            {"name": "negatives", "args": [[10, -4, 1]], "expected": [10, 6, 7], "public": False},
            {"name": "zeros", "args": [[0, 0, 3]], "expected": [0, 0, 3], "public": False},
        ],
    },
    {
        "title": "Palindrome Check",
        "summary": "Does the word read the same backwards?",
        "description": (
            "Write `solution` to return `true` when the input string is a palindrome and `false` "
            "otherwise.\n\n"
            "Comparison is exact: no case folding, no stripping of spaces. An empty string is a "
            "palindrome."
        ),
        "difficulty": "beginner",
        "category": "algorithms",
        "points": 20,
        "topics": ["strings", "two pointers"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(text) {\n  // return true or false\n}\n",
            "python": "def solution(text):\n    # return True or False\n",
        },
        "examples": [{"input": ["racecar"], "output": True}, {"input": ["hello"], "output": False}],
        "hints": ["Compare the string with its reverse, or walk two pointers in from each end."],
        "tests": [
            {"name": "racecar", "args": ["racecar"], "expected": True, "public": True},
            {"name": "hello", "args": ["hello"], "expected": False, "public": True},
            {"name": "empty", "args": [""], "expected": True, "public": False},
            {"name": "even length", "args": ["noon"], "expected": True, "public": False},
            {"name": "case matters", "args": ["Noon"], "expected": False, "public": False},
        ],
    },
    {
        "title": "Remove Duplicates",
        "summary": "Keep each value once, in original order.",
        "description": (
            "Write `solution` to return the array with repeated values removed.\n\n"
            "Keep the first occurrence of every value and preserve the original order. Do not sort "
            "the result."
        ),
        "difficulty": "intermediate",
        "category": "data",
        "points": 30,
        "topics": ["arrays", "sets"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(items) {\n  // return items with duplicates removed\n}\n",
            "python": "def solution(items):\n    # return items with duplicates removed, order preserved\n",
        },
        "examples": [
            {"input": [[1, 1, 2, 3, 3, 2]], "output": [1, 2, 3]},
            {"input": [["a", "a", "b"]], "output": ["a", "b"]},
        ],
        "hints": [
            "Track what you have already seen in a Set, and only push values that are new.",
            "JavaScript's [...new Set(items)] also keeps insertion order.",
        ],
        "tests": [
            {"name": "numbers", "args": [[1, 1, 2, 3, 3, 2]], "expected": [1, 2, 3], "public": True},
            {"name": "strings", "args": [["a", "a", "b"]], "expected": ["a", "b"], "public": True},
            {"name": "nothing to remove", "args": [[1, 2, 3]], "expected": [1, 2, 3], "public": False},
            {"name": "all the same", "args": [[7, 7, 7]], "expected": [7], "public": False},
            {"name": "empty", "args": [[]], "expected": [], "public": False},
        ],
    },
    {
        "title": "Two Sum Indices",
        "summary": "Find the two positions that add up to the target.",
        "description": (
            "Write `solution` that receives an array of numbers and a target number. Return a "
            "two-element array with the indices of the two values that add up to the target.\n\n"
            "Exactly one valid pair exists, and an element cannot be paired with itself. Return the "
            "indices in ascending order."
        ),
        "difficulty": "intermediate",
        "category": "algorithms",
        "points": 40,
        "topics": ["hash maps", "arrays"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(numbers, target) {\n  // return [indexA, indexB]\n}\n",
            "python": "def solution(numbers, target):\n    # return [index_a, index_b]\n",
        },
        "examples": [
            {"input": [[2, 7, 11, 15], 9], "output": [0, 1]},
            {"input": [[3, 2, 4], 6], "output": [1, 2]},
        ],
        "hints": [
            "A double loop works but is O(n²). Try one pass with a dictionary of `needed -> index`.",
            "For each value, the partner you want is target - value.",
        ],
        "tests": [
            {"name": "first pair", "args": [[2, 7, 11, 15], 9], "expected": [0, 1], "public": True},
            {"name": "later pair", "args": [[3, 2, 4], 6], "expected": [1, 2], "public": True},
            {"name": "negatives", "args": [[-4, 4, 1, 8], 5], "expected": [1, 2], "public": False},
            {"name": "duplicated values", "args": [[3, 3], 6], "expected": [0, 1], "public": False},
            {"name": "far apart", "args": [[1, 5, 9, 3, 13], 12], "expected": [2, 3], "public": False},
        ],
    },
    {
        "title": "Valid Parentheses",
        "summary": "Do every bracket close in the right order?",
        "description": (
            "Write `solution` to return `true` when a string of brackets is balanced, `false` "
            "otherwise. The only characters are ( ) [ ] { }.\n\n"
            "A closing bracket must match the most recent unmatched opener. An empty string counts "
            "as balanced."
        ),
        "difficulty": "intermediate",
        "category": "data",
        "points": 40,
        "topics": ["stacks"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(text) {\n  // return true or false\n}\n",
            "python": "def solution(text):\n    # return True or False\n",
        },
        "examples": [
            {"input": ["([]{})"], "output": True},
            {"input": ["(]"], "output": False},
        ],
        "hints": [
            "Push openers onto a stack; for each closer, check the top of the stack.",
            "The string is balanced only if the stack is empty at the end.",
        ],
        "tests": [
            {"name": "nested mix", "args": ["([]{})"], "expected": True, "public": True},
            {"name": "wrong order", "args": ["(]"], "expected": False, "public": True},
            {"name": "empty", "args": [""], "expected": True, "public": False},
            {"name": "never closed", "args": ["((()"], "expected": False, "public": False},
            {"name": "sequence", "args": ["()[]{}"], "expected": True, "public": False},
            {"name": "interleaved", "args": ["([)]"], "expected": False, "public": False},
        ],
    },
    {
        "title": "Title Case",
        "summary": "Capitalise the first letter of every word.",
        "description": (
            "Write `solution` to return the sentence with the first character of each word upperised "
            "and the remaining characters of that word lowercased.\n\n"
            "Words are separated by single spaces, and the number of spaces must not change."
        ),
        "difficulty": "intermediate",
        "category": "python",
        "points": 30,
        "topics": ["strings", "case"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(sentence) {\n  // return the title-cased sentence\n}\n",
            "python": "def solution(sentence):\n    # return the title-cased sentence\n",
        },
        "examples": [
            {"input": ["hello world"], "output": "Hello World"},
            {"input": ["aQi uSD"], "output": "Aqi Usd"},
        ],
        "hints": ["Split on the space, transform each word, then join with a single space."],
        "tests": [
            {"name": "two words", "args": ["hello world"], "expected": "Hello World", "public": True},
            {"name": "odd casing", "args": ["aQi uSD"], "expected": "Aqi Usd", "public": True},
            {"name": "one word", "args": ["codeher"], "expected": "Codeher", "public": False},
            {"name": "empty", "args": [""], "expected": "", "public": False},
            {"name": "already done", "args": ["Already Done"], "expected": "Already Done", "public": False},
        ],
    },
    {
        "title": "FizzBuzz List",
        "summary": "Build the classic list as strings.",
        "description": (
            "Write `solution` that receives a positive integer `n` and returns an array of length "
            "`n`.\n\n"
            "At position i (counting from 1) put 'Fizz' if the number is divisible by 3, 'Buzz' if "
            "divisible by 5, 'FizzBuzz' if divisible by both, otherwise the number itself as a "
            "string."
        ),
        "difficulty": "intermediate",
        "category": "algorithms",
        "points": 35,
        "topics": ["loops", "modulo"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(n) {\n  // return an array of n strings\n}\n",
            "python": "def solution(n):\n    # return a list of n strings\n",
        },
        "examples": [
            {"input": [5], "output": ["1", "2", "Fizz", "4", "Buzz"]},
            {"input": [1], "output": ["1"]},
        ],
        "hints": ["Check divisibility by 15 first, otherwise 'FizzBuzz' is unreachable."],
        "tests": [
            {"name": "up to five", "args": [5], "expected": ["1", "2", "Fizz", "4", "Buzz"], "public": True},
            {"name": "one", "args": [1], "expected": ["1"], "public": True},
            {
                "name": "fifteen",
                "args": [15],
                "expected": ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"],
                "public": False,
            },
            {"name": "three", "args": [3], "expected": ["1", "2", "Fizz"], "public": False},
        ],
    },
    {
        "title": "Flatten One Level",
        "summary": "Unwrap exactly one layer of nesting.",
        "description": (
            "Write `solution` to return a new array where any nested array has been expanded in "
            "place, exactly one level deep.\n\n"
            "There is never more than one level of nesting in the input, and you must not mutate it."
        ),
        "difficulty": "advanced",
        "category": "data",
        "points": 50,
        "topics": ["arrays", "spread"],
        "allowed_languages": ["javascript", "python"],
        "starter": {
            "javascript": "function solution(items) {\n  // flatten one level and return a new array\n}\n",
            "python": "def solution(items):\n    # flatten one level and return a new list\n",
        },
        "examples": [
            {"input": [[1, [2, 3], 4]], "output": [1, 2, 3, 4]},
            {"input": [[[], [1]]], "output": [1]},
        ],
        "hints": [
            "In JavaScript, Array.isArray(value) tells you whether to spread it.",
            "In Python, loop and use list(value) when isinstance(value, list).",
        ],
        "tests": [
            {"name": "simple mix", "args": [[1, [2, 3], 4]], "expected": [1, 2, 3, 4], "public": True},
            {"name": "empty nested", "args": [[[], [1]]], "expected": [1], "public": True},
            {"name": "already flat", "args": [[1, 2]], "expected": [1, 2], "public": False},
            {"name": "empty array", "args": [[]], "expected": [], "public": False},
            {"name": "strings", "args": [["a", ["b", "c"]]], "expected": ["a", "b", "c"], "public": False},
            {"name": "nested empties", "args": [[[], []]], "expected": [], "public": False},
        ],
    },
]
