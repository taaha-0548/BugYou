-- BugYou Database Setup Script v4.0
-- Simplified schema with essential fields only

-- Drop all tables
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS python_basic CASCADE;
DROP TABLE IF EXISTS python_intermediate CASCADE;
DROP TABLE IF EXISTS python_advanced CASCADE;
DROP TABLE IF EXISTS javascript_basic CASCADE;
DROP TABLE IF EXISTS javascript_intermediate CASCADE;
DROP TABLE IF EXISTS javascript_advanced CASCADE;
DROP TABLE IF EXISTS java_basic CASCADE;
DROP TABLE IF EXISTS java_intermediate CASCADE;
DROP TABLE IF EXISTS java_advanced CASCADE;
DROP TABLE IF EXISTS cpp_basic CASCADE;
DROP TABLE IF EXISTS cpp_intermediate CASCADE;
DROP TABLE IF EXISTS cpp_advanced CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create minimal users table for created_by reference
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password TEXT,
    emailaddress TEXT UNIQUE NOT NULL,
    fullname TEXT NOT NULL,
);

-- Base challenge table template
CREATE TABLE python_basic (
    challenge_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    problem_statement TEXT NOT NULL,
    buggy_code TEXT NOT NULL,
    reference_solution TEXT,
    solution_explanation TEXT,
    hint_1 TEXT,
    hint_2 TEXT,
    hint_3 TEXT,
    learning_objectives TEXT,
    max_score INTEGER DEFAULT 10,
    test_case_1_input TEXT NOT NULL,
    test_case_1_expected TEXT NOT NULL,
    test_case_2_input TEXT NOT NULL,
    test_case_2_expected TEXT NOT NULL,
    test_case_3_input TEXT NOT NULL,
    test_case_3_expected TEXT NOT NULL,
    test_case_4_input TEXT,
    test_case_4_expected TEXT,
    test_case_5_input TEXT,
    test_case_5_expected TEXT,
    hidden_test_1_input TEXT,
    hidden_test_1_expected TEXT,
    hidden_test_2_input TEXT,
    hidden_test_2_expected TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_attempts DECIMAL(5,2) DEFAULT 0.0
);

-- Create other language tables with the same structure
CREATE TABLE python_intermediate (LIKE python_basic INCLUDING ALL);
CREATE TABLE python_advanced (LIKE python_basic INCLUDING ALL);
CREATE TABLE javascript_basic (LIKE python_basic INCLUDING ALL);
CREATE TABLE javascript_intermediate (LIKE python_basic INCLUDING ALL);
CREATE TABLE javascript_advanced (LIKE python_basic INCLUDING ALL);
CREATE TABLE java_basic (LIKE python_basic INCLUDING ALL);
CREATE TABLE java_intermediate (LIKE python_basic INCLUDING ALL);
CREATE TABLE java_advanced (LIKE python_basic INCLUDING ALL);
CREATE TABLE cpp_basic (LIKE python_basic INCLUDING ALL);
CREATE TABLE cpp_intermediate (LIKE python_basic INCLUDING ALL);
CREATE TABLE cpp_advanced (LIKE python_basic INCLUDING ALL); 
CREATE TABLE users (LIKE python_basic INCLUDING ALL); 