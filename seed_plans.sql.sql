INSERT INTO plans (name, slug, track, price_monthly, credits_monthly, max_team_size, features) VALUES
('Basic', 'basic', 'individual', 4.99, 50, 1, 
'{"filters": {"age_range": false, "income_level": false, "education": false, "occupation": false, "marital_status": false, "big_five": false, "price_sensitivity": false}, "reports": {"screen": true, "pdf": false, "dashboard": false, "custom": false}, "tests": {"single": true, "ab_compare": false, "multi_compare": false}, "api_access": false, "max_personas_per_query": 50}'),

('Pro', 'pro', 'individual', 9.99, 100, 1, 
'{"filters": {"age_range": true, "income_level": true, "education": false, "occupation": false, "marital_status": false, "big_five": false, "price_sensitivity": true}, "reports": {"screen": true, "pdf": true, "dashboard": false, "custom": false}, "tests": {"single": true, "ab_compare": true, "multi_compare": false}, "api_access": false, "max_personas_per_query": 100}'),

('Business', 'business', 'individual', 19.99, 250, 3, 
'{"filters": {"age_range": true, "income_level": true, "education": true, "occupation": true, "marital_status": true, "big_five": true, "price_sensitivity": true}, "reports": {"screen": true, "pdf": true, "dashboard": true, "custom": false}, "tests": {"single": true, "ab_compare": true, "multi_compare": true}, "api_access": false, "max_personas_per_query": 250}'),

('Enterprise', 'enterprise', 'individual', 49.99, 1000, 5, 
'{"filters": {"age_range": true, "income_level": true, "education": true, "occupation": true, "marital_status": true, "big_five": true, "price_sensitivity": true}, "reports": {"screen": true, "pdf": true, "dashboard": true, "custom": true}, "tests": {"single": true, "ab_compare": true, "multi_compare": true}, "api_access": true, "max_personas_per_query": 500}');