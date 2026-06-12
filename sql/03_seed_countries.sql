-- =============================================================================
-- Seed: target countries for the Global AI Conversation Analytics Platform
--
-- iso_code       : ISO 3166-1 alpha-3 (used by Plotly choropleth / globe page)
-- default_language: BCP-47 primary language tag
-- ON CONFLICT    : idempotent — safe to re-run after schema migrations
-- =============================================================================

INSERT INTO countries (country_name, iso_code, region, default_language) VALUES
('United States',  'USA', 'North America', 'en'),
('Canada',         'CAN', 'North America', 'en'),
('United Kingdom', 'GBR', 'Europe',        'en'),
('China',          'CHN', 'Asia',          'zh'),
('Russia',         'RUS', 'Europe/Asia',   'ru'),
('France',         'FRA', 'Europe',        'fr'),
('Brazil',         'BRA', 'South America', 'pt'),
('Japan',          'JPN', 'Asia',          'ja')
ON CONFLICT (country_name) DO UPDATE
    SET iso_code         = EXCLUDED.iso_code,
        region           = EXCLUDED.region,
        default_language = EXCLUDED.default_language;
