import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.practice import PracticeProblem

PROBLEMS = [
    {
        'title': 'Two Sum',
        'level': 'beginner',
        'difficulty': 'Easy',
        'tags': ['arrays', 'hash-map'],
        'description': 'Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target.',
        'starter_code': 'public class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{};\n    }\n}\n',
        'constraints': 'Each input has exactly one solution.',
        'expected_output': '[0,1]',
        'test_cases': [
            {'input': 'nums=[2,7,11,15], target=9', 'output': '[0,1]'},
            {'input': 'nums=[3,2,4], target=6', 'output': '[1,2]'}
        ]
    },
    {
        'title': 'Reverse String',
        'level': 'beginner',
        'difficulty': 'Easy',
        'tags': ['strings'],
        'description': 'Reverse a string in place.',
        'starter_code': 'public class Solution {\n    public void reverseString(char[] s) {\n    }\n}\n',
        'constraints': 'Do it in-place with O(1) extra memory.',
        'expected_output': '["o","l","l","e","h"]',
        'test_cases': [
            {'input': 's=["h","e","l","l","o"]', 'output': '["o","l","l","e","h"]'}
        ]
    },
    {
        'title': 'Binary Search',
        'level': 'intermediate',
        'difficulty': 'Medium',
        'tags': ['arrays', 'binary-search'],
        'description': 'Given a sorted array and a target, return its index or -1.',
        'starter_code': 'public class Solution {\n    public int search(int[] nums, int target) {\n        return -1;\n    }\n}\n',
        'constraints': 'Array is sorted in ascending order.',
        'expected_output': '4',
        'test_cases': [
            {'input': 'nums=[-1,0,3,5,9,12], target=9', 'output': '4'}
        ]
    },
    {
        'title': 'Valid Parentheses',
        'level': 'intermediate',
        'difficulty': 'Medium',
        'tags': ['stack', 'strings'],
        'description': 'Return true if the parentheses are valid.',
        'starter_code': 'public class Solution {\n    public boolean isValid(String s) {\n        return false;\n    }\n}\n',
        'constraints': 's consists of parentheses only.',
        'expected_output': 'true',
        'test_cases': [
            {'input': 's="()[]{}"', 'output': 'true'},
            {'input': 's="(]"', 'output': 'false'}
        ]
    },
    {
        'title': 'Longest Substring Without Repeating Characters',
        'level': 'advanced',
        'difficulty': 'Hard',
        'tags': ['sliding-window', 'strings'],
        'description': 'Find the length of the longest substring without repeating characters.',
        'starter_code': 'public class Solution {\n    public int lengthOfLongestSubstring(String s) {\n        return 0;\n    }\n}\n',
        'constraints': '0 <= s.length <= 5 * 10^4',
        'expected_output': '3',
        'test_cases': [
            {'input': 's="abcabcbb"', 'output': '3'},
            {'input': 's="bbbbb"', 'output': '1'}
        ]
    },
    {
        'title': 'LRU Cache',
        'level': 'advanced',
        'difficulty': 'Hard',
        'tags': ['design', 'hash-map', 'linked-list'],
        'description': 'Design a data structure that follows the LRU cache constraint.',
        'starter_code': 'import java.util.*;\npublic class LRUCache {\n    public LRUCache(int capacity) {\n    }\n    public int get(int key) {\n        return -1;\n    }\n    public void put(int key, int value) {\n    }\n}\n',
        'constraints': 'Both get and put must run in O(1) average time.',
        'expected_output': '[null,null,null,1,-1,null,2,null,3,4]',
        'test_cases': [
            {'input': 'capacity=2, ops=[[put,1,1],[put,2,2],[get,1],[put,3,3],[get,2],[put,4,4],[get,1],[get,3],[get,4]]', 'output': '[null,null,null,1,-1,null,2,null,3,4]'}
        ]
    }
]

def seed():
    app = create_app()
    with app.app_context():
        added = 0
        skipped = 0
        for data in PROBLEMS:
            exists = PracticeProblem.query.filter_by(title=data['title']).first()
            if exists:
                skipped += 1
                continue
            db.session.add(PracticeProblem(**data))
            added += 1
        db.session.commit()
        print(f'Seeded {added} problems. Skipped {skipped} existing.')

if __name__ == '__main__':
    seed()
