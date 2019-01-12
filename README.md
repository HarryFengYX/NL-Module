# NL-Module
This module send a request to Google Natural Language API, and parse the returned data to a desirable format. _Client secret json_ was deleted.

This module takes natural language text (support multiple sentences) as input. The output is a json file wrote in the end, which contains the main verbs, main subjects, and everything that depends on them. What depends on them is labeled with a "condition" like "whose", "prep" according to the dependency edge label.

Sample input: "it is lunch time. find the dinning menu"

Sample output: `[{"main subjects": [{"lemma": "it"}], "nsubj": "it", "root": "is", "main verbs": [{"lemma": "be", "dependencies": [{"lemma": "time", "dependencies": [{"lemma": "lunch", "pos tag": "noun", "condition": "description"}], "pos tag": "noun", "condition": "dependency"}, {"lemma": ".", "pos tag": "punct", "condition": "dependency"}]}]}, {"main subjects": [null], "nsubj": "None", "root": "find", "main verbs": [{"lemma": "find", "dependencies": [{"lemma": "menu", "dependencies": [{"lemma": "dinning", "pos tag": "noun", "condition": "description"}], "pos tag": "noun", "condition": "object"}]}]}]`
