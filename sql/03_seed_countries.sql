INSERT INTO countries (country_name, iso_code, region, default_language) VALUES
('United States', 'USA', 'North America', 'en'),
('Canada', 'CAN', 'North America', 'en'),
('United Kingdom', 'GBR', 'Europe', 'en'),
('China', 'CHN', 'Asia', 'zh'),
('Russia', 'RUS', 'Europe/Asia', 'ru'),
('France', 'FRA', 'Europe', 'fr'),
('Brazil', 'BRA', 'South America', 'pt'),
('Japan', 'JPN', 'Asia', 'ja')
ON CONFLICT (country_name) DO NOTHING;
