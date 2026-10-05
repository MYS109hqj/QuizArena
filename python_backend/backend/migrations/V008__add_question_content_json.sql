ALTER TABLE new_quiz_questions
    ADD COLUMN content_json LONGTEXT NULL AFTER correct_answer_json;

UPDATE new_quiz_questions SET content_json = '{}' WHERE content_json IS NULL;

ALTER TABLE new_quiz_questions MODIFY COLUMN content_json LONGTEXT NOT NULL;
