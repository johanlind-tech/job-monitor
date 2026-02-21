-- 001_initial_schema.sql
-- Multi-user SaaS job digest platform schema

-- ============================================================
-- ENUM TYPE
-- ============================================================

CREATE TYPE subscription_status AS ENUM ('trialing', 'active', 'canceled');

-- ============================================================
-- TABLES
-- ============================================================

-- profiles: extends Supabase Auth auth.users
CREATE TABLE profiles (
    id          uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    email       text,
    stripe_customer_id   text,
    subscription_status  subscription_status DEFAULT 'trialing',
    plan                 text DEFAULT 'monthly' CHECK (plan IN ('monthly', 'quarterly', 'annual')),
    trial_ends_at        timestamptz,
    created_at           timestamptz DEFAULT now()
);

-- user_preferences: per-user filter/delivery settings
CREATE TABLE user_preferences (
    user_id             uuid PRIMARY KEY REFERENCES profiles (id) ON DELETE CASCADE,
    delivery_days       int[] DEFAULT '{1,2,3,4,5}',
    keywords_include    text[],
    keywords_exclude    text[],
    sources_enabled     text[],
    regions             text[] DEFAULT '{}',
    municipalities      text[] DEFAULT '{}',
    employment_types    text[] DEFAULT '{"permanent","interim"}'
);

-- jobs: global deduplication table
CREATE TABLE jobs (
    id              text PRIMARY KEY,  -- MD5 hash of URL
    title           text,
    company         text,
    url             text,
    source          text,
    country         text DEFAULT 'SE',
    municipality_code text,
    lan_code        text,
    location_raw    text,
    employment_type text,
    first_seen_at   timestamptz DEFAULT now()
);

-- user_job_queue: per-user delivery queue
CREATE TABLE user_job_queue (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id   uuid NOT NULL REFERENCES profiles (id) ON DELETE CASCADE,
    job_id    text NOT NULL REFERENCES jobs (id) ON DELETE CASCADE,
    queued_at timestamptz DEFAULT now(),
    sent_at   timestamptz,
    CONSTRAINT uq_user_job UNIQUE (user_id, job_id)
);

-- swedish_locations: lookup table for location parsing and UI
CREATE TABLE swedish_locations (
    municipality_code text PRIMARY KEY,
    municipality_name text NOT NULL,
    lan_code          text NOT NULL,
    lan_name          text NOT NULL
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_user_job_queue_user_sent ON user_job_queue (user_id, sent_at);
CREATE INDEX idx_jobs_source_first_seen   ON jobs (source, first_seen_at);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs             ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_job_queue   ENABLE ROW LEVEL SECURITY;
ALTER TABLE swedish_locations ENABLE ROW LEVEL SECURITY;

-- profiles: users can read/update only their own row
CREATE POLICY profiles_select ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY profiles_update ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- user_preferences: users can read/update only their own row
CREATE POLICY user_preferences_select ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY user_preferences_update ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- jobs: all authenticated users can read
CREATE POLICY jobs_select ON jobs
    FOR SELECT TO authenticated
    USING (true);

-- user_job_queue: users can read only their own rows
CREATE POLICY user_job_queue_select ON user_job_queue
    FOR SELECT USING (auth.uid() = user_id);

-- swedish_locations: all authenticated users can read
CREATE POLICY swedish_locations_select ON swedish_locations
    FOR SELECT TO authenticated
    USING (true);

-- ============================================================
-- TRIGGER: auto-create profile + preferences on auth.users insert
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, subscription_status, trial_ends_at, created_at)
    VALUES (
        NEW.id,
        NEW.email,
        'trialing',
        now() + interval '14 days',
        now()
    );

    INSERT INTO public.user_preferences (
        user_id,
        delivery_days,
        keywords_include,
        keywords_exclude,
        sources_enabled,
        regions,
        municipalities,
        employment_types
    ) VALUES (
        NEW.id,
        '{1,2,3,4,5}',
        ARRAY[
            'CEO','Country Manager','General Manager','Managing Director',
            'Business Unit Director','BU Director','Vice President','VP',
            'Senior Vice President','SVP','CMO','CCO','CSO','CBDO',
            'Commercial Director','Marketing Director','Commercial Lead',
            'Head of Commercial','Head of Marketing',
            'VD','Landschef','Affärsområdesdirektör','Affärsområdeschef',
            'Marknadsdirektör','Kommersiell direktör',
            'Affärsutvecklingsdirektör','Försäljningsdirektör'
        ],
        ARRAY['junior','assistant','coordinator','assisterande','assistent'],
        '{}',   -- sources_enabled: empty = all sources
        '{}',   -- regions: empty = all
        '{}',   -- municipalities: empty = all
        '{"permanent","interim"}'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- SEED: swedish_locations (all 290 municipalities across 21 län)
-- ============================================================

-- Stockholms län (26 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0114', 'Upplands Väsby', '01', 'Stockholms län'),
('0115', 'Vallentuna', '01', 'Stockholms län'),
('0117', 'Österåker', '01', 'Stockholms län'),
('0120', 'Värmdö', '01', 'Stockholms län'),
('0123', 'Järfälla', '01', 'Stockholms län'),
('0125', 'Ekerö', '01', 'Stockholms län'),
('0126', 'Huddinge', '01', 'Stockholms län'),
('0127', 'Botkyrka', '01', 'Stockholms län'),
('0128', 'Salem', '01', 'Stockholms län'),
('0136', 'Haninge', '01', 'Stockholms län'),
('0138', 'Tyresö', '01', 'Stockholms län'),
('0139', 'Upplands-Bro', '01', 'Stockholms län'),
('0140', 'Nykvarn', '01', 'Stockholms län'),
('0160', 'Täby', '01', 'Stockholms län'),
('0162', 'Danderyd', '01', 'Stockholms län'),
('0163', 'Sollentuna', '01', 'Stockholms län'),
('0180', 'Stockholm', '01', 'Stockholms län'),
('0181', 'Södertälje', '01', 'Stockholms län'),
('0182', 'Nacka', '01', 'Stockholms län'),
('0183', 'Sundbyberg', '01', 'Stockholms län'),
('0184', 'Solna', '01', 'Stockholms län'),
('0186', 'Lidingö', '01', 'Stockholms län'),
('0187', 'Vaxholm', '01', 'Stockholms län'),
('0188', 'Norrtälje', '01', 'Stockholms län'),
('0191', 'Sigtuna', '01', 'Stockholms län'),
('0192', 'Nynäshamn', '01', 'Stockholms län');

-- Uppsala län (8 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0305', 'Håbo', '03', 'Uppsala län'),
('0319', 'Älvkarleby', '03', 'Uppsala län'),
('0330', 'Knivsta', '03', 'Uppsala län'),
('0331', 'Heby', '03', 'Uppsala län'),
('0360', 'Tierp', '03', 'Uppsala län'),
('0380', 'Uppsala', '03', 'Uppsala län'),
('0381', 'Enköping', '03', 'Uppsala län'),
('0382', 'Östhammar', '03', 'Uppsala län');

-- Södermanlands län (9 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0428', 'Vingåker', '04', 'Södermanlands län'),
('0461', 'Gnesta', '04', 'Södermanlands län'),
('0480', 'Nyköping', '04', 'Södermanlands län'),
('0481', 'Oxelösund', '04', 'Södermanlands län'),
('0482', 'Flen', '04', 'Södermanlands län'),
('0483', 'Katrineholm', '04', 'Södermanlands län'),
('0484', 'Eskilstuna', '04', 'Södermanlands län'),
('0486', 'Strängnäs', '04', 'Södermanlands län'),
('0488', 'Trosa', '04', 'Södermanlands län');

-- Östergötlands län (13 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0509', 'Ödeshög', '05', 'Östergötlands län'),
('0512', 'Ydre', '05', 'Östergötlands län'),
('0513', 'Kinda', '05', 'Östergötlands län'),
('0560', 'Boxholm', '05', 'Östergötlands län'),
('0561', 'Åtvidaberg', '05', 'Östergötlands län'),
('0562', 'Finspång', '05', 'Östergötlands län'),
('0563', 'Valdemarsvik', '05', 'Östergötlands län'),
('0580', 'Linköping', '05', 'Östergötlands län'),
('0581', 'Norrköping', '05', 'Östergötlands län'),
('0582', 'Söderköping', '05', 'Östergötlands län'),
('0583', 'Motala', '05', 'Östergötlands län'),
('0584', 'Vadstena', '05', 'Östergötlands län'),
('0586', 'Mjölby', '05', 'Östergötlands län');

-- Jönköpings län (13 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0604', 'Aneby', '06', 'Jönköpings län'),
('0617', 'Gnosjö', '06', 'Jönköpings län'),
('0642', 'Mullsjö', '06', 'Jönköpings län'),
('0643', 'Habo', '06', 'Jönköpings län'),
('0662', 'Gislaved', '06', 'Jönköpings län'),
('0665', 'Vaggeryd', '06', 'Jönköpings län'),
('0680', 'Jönköping', '06', 'Jönköpings län'),
('0682', 'Nässjö', '06', 'Jönköpings län'),
('0683', 'Värnamo', '06', 'Jönköpings län'),
('0684', 'Sävsjö', '06', 'Jönköpings län'),
('0685', 'Vetlanda', '06', 'Jönköpings län'),
('0686', 'Eksjö', '06', 'Jönköpings län'),
('0687', 'Tranås', '06', 'Jönköpings län');

-- Kronobergs län (8 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0760', 'Uppvidinge', '07', 'Kronobergs län'),
('0761', 'Lessebo', '07', 'Kronobergs län'),
('0763', 'Tingsryd', '07', 'Kronobergs län'),
('0764', 'Alvesta', '07', 'Kronobergs län'),
('0765', 'Älmhult', '07', 'Kronobergs län'),
('0767', 'Markaryd', '07', 'Kronobergs län'),
('0780', 'Växjö', '07', 'Kronobergs län'),
('0781', 'Ljungby', '07', 'Kronobergs län');

-- Kalmar län (12 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0821', 'Högsby', '08', 'Kalmar län'),
('0834', 'Torsås', '08', 'Kalmar län'),
('0840', 'Mörbylånga', '08', 'Kalmar län'),
('0860', 'Hultsfred', '08', 'Kalmar län'),
('0861', 'Mönsterås', '08', 'Kalmar län'),
('0862', 'Emmaboda', '08', 'Kalmar län'),
('0880', 'Kalmar', '08', 'Kalmar län'),
('0881', 'Nybro', '08', 'Kalmar län'),
('0882', 'Oskarshamn', '08', 'Kalmar län'),
('0883', 'Västervik', '08', 'Kalmar län'),
('0884', 'Vimmerby', '08', 'Kalmar län'),
('0885', 'Borgholm', '08', 'Kalmar län');

-- Gotlands län (1 municipality)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('0980', 'Gotland', '09', 'Gotlands län');

-- Blekinge län (5 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1060', 'Olofström', '10', 'Blekinge län'),
('1080', 'Karlskrona', '10', 'Blekinge län'),
('1081', 'Ronneby', '10', 'Blekinge län'),
('1082', 'Karlshamn', '10', 'Blekinge län'),
('1083', 'Sölvesborg', '10', 'Blekinge län');

-- Skåne län (33 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1214', 'Svalöv', '12', 'Skåne län'),
('1230', 'Staffanstorp', '12', 'Skåne län'),
('1231', 'Burlöv', '12', 'Skåne län'),
('1233', 'Vellinge', '12', 'Skåne län'),
('1256', 'Östra Göinge', '12', 'Skåne län'),
('1257', 'Örkelljunga', '12', 'Skåne län'),
('1260', 'Bjuv', '12', 'Skåne län'),
('1261', 'Kävlinge', '12', 'Skåne län'),
('1262', 'Lomma', '12', 'Skåne län'),
('1263', 'Svedala', '12', 'Skåne län'),
('1264', 'Skurup', '12', 'Skåne län'),
('1265', 'Sjöbo', '12', 'Skåne län'),
('1266', 'Hörby', '12', 'Skåne län'),
('1267', 'Höör', '12', 'Skåne län'),
('1270', 'Tomelilla', '12', 'Skåne län'),
('1272', 'Bromölla', '12', 'Skåne län'),
('1273', 'Osby', '12', 'Skåne län'),
('1275', 'Perstorp', '12', 'Skåne län'),
('1276', 'Klippan', '12', 'Skåne län'),
('1277', 'Åstorp', '12', 'Skåne län'),
('1278', 'Båstad', '12', 'Skåne län'),
('1280', 'Malmö', '12', 'Skåne län'),
('1281', 'Lund', '12', 'Skåne län'),
('1282', 'Landskrona', '12', 'Skåne län'),
('1283', 'Helsingborg', '12', 'Skåne län'),
('1284', 'Höganäs', '12', 'Skåne län'),
('1285', 'Eslöv', '12', 'Skåne län'),
('1286', 'Ystad', '12', 'Skåne län'),
('1287', 'Trelleborg', '12', 'Skåne län'),
('1290', 'Kristianstad', '12', 'Skåne län'),
('1291', 'Simrishamn', '12', 'Skåne län'),
('1292', 'Ängelholm', '12', 'Skåne län'),
('1293', 'Hässleholm', '12', 'Skåne län');

-- Hallands län (6 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1315', 'Hylte', '13', 'Hallands län'),
('1380', 'Halmstad', '13', 'Hallands län'),
('1381', 'Laholm', '13', 'Hallands län'),
('1382', 'Falkenberg', '13', 'Hallands län'),
('1383', 'Varberg', '13', 'Hallands län'),
('1384', 'Kungsbacka', '13', 'Hallands län');

-- Västra Götalands län (49 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1401', 'Härryda', '14', 'Västra Götalands län'),
('1402', 'Partille', '14', 'Västra Götalands län'),
('1407', 'Öckerö', '14', 'Västra Götalands län'),
('1415', 'Stenungsund', '14', 'Västra Götalands län'),
('1419', 'Tjörn', '14', 'Västra Götalands län'),
('1421', 'Orust', '14', 'Västra Götalands län'),
('1427', 'Sotenäs', '14', 'Västra Götalands län'),
('1430', 'Munkedal', '14', 'Västra Götalands län'),
('1435', 'Tanum', '14', 'Västra Götalands län'),
('1438', 'Dals-Ed', '14', 'Västra Götalands län'),
('1439', 'Färgelanda', '14', 'Västra Götalands län'),
('1440', 'Ale', '14', 'Västra Götalands län'),
('1441', 'Lerum', '14', 'Västra Götalands län'),
('1442', 'Vårgårda', '14', 'Västra Götalands län'),
('1443', 'Bollebygd', '14', 'Västra Götalands län'),
('1444', 'Grästorp', '14', 'Västra Götalands län'),
('1445', 'Essunga', '14', 'Västra Götalands län'),
('1446', 'Karlsborg', '14', 'Västra Götalands län'),
('1447', 'Gullspång', '14', 'Västra Götalands län'),
('1452', 'Tranemo', '14', 'Västra Götalands län'),
('1460', 'Bengtsfors', '14', 'Västra Götalands län'),
('1461', 'Mellerud', '14', 'Västra Götalands län'),
('1462', 'Lilla Edet', '14', 'Västra Götalands län'),
('1463', 'Mark', '14', 'Västra Götalands län'),
('1465', 'Svenljunga', '14', 'Västra Götalands län'),
('1466', 'Herrljunga', '14', 'Västra Götalands län'),
('1470', 'Vara', '14', 'Västra Götalands län'),
('1471', 'Götene', '14', 'Västra Götalands län'),
('1472', 'Tibro', '14', 'Västra Götalands län'),
('1473', 'Töreboda', '14', 'Västra Götalands län'),
('1480', 'Göteborg', '14', 'Västra Götalands län'),
('1481', 'Mölndal', '14', 'Västra Götalands län'),
('1482', 'Kungälv', '14', 'Västra Götalands län'),
('1484', 'Lysekil', '14', 'Västra Götalands län'),
('1485', 'Uddevalla', '14', 'Västra Götalands län'),
('1486', 'Strömstad', '14', 'Västra Götalands län'),
('1487', 'Vänersborg', '14', 'Västra Götalands län'),
('1488', 'Trollhättan', '14', 'Västra Götalands län'),
('1489', 'Alingsås', '14', 'Västra Götalands län'),
('1490', 'Borås', '14', 'Västra Götalands län'),
('1491', 'Ulricehamn', '14', 'Västra Götalands län'),
('1492', 'Åmål', '14', 'Västra Götalands län'),
('1493', 'Mariestad', '14', 'Västra Götalands län'),
('1494', 'Lidköping', '14', 'Västra Götalands län'),
('1495', 'Skara', '14', 'Västra Götalands län'),
('1496', 'Skövde', '14', 'Västra Götalands län'),
('1497', 'Hjo', '14', 'Västra Götalands län'),
('1498', 'Tidaholm', '14', 'Västra Götalands län'),
('1499', 'Falköping', '14', 'Västra Götalands län');

-- Värmlands län (16 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1715', 'Kil', '17', 'Värmlands län'),
('1730', 'Eda', '17', 'Värmlands län'),
('1737', 'Torsby', '17', 'Värmlands län'),
('1760', 'Storfors', '17', 'Värmlands län'),
('1761', 'Hammarö', '17', 'Värmlands län'),
('1762', 'Munkfors', '17', 'Värmlands län'),
('1763', 'Forshaga', '17', 'Värmlands län'),
('1764', 'Grums', '17', 'Värmlands län'),
('1765', 'Årjäng', '17', 'Värmlands län'),
('1766', 'Sunne', '17', 'Värmlands län'),
('1780', 'Karlstad', '17', 'Värmlands län'),
('1781', 'Kristinehamn', '17', 'Värmlands län'),
('1782', 'Filipstad', '17', 'Värmlands län'),
('1783', 'Hagfors', '17', 'Värmlands län'),
('1784', 'Arvika', '17', 'Värmlands län'),
('1785', 'Säffle', '17', 'Värmlands län');

-- Örebro län (12 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1814', 'Lekeberg', '18', 'Örebro län'),
('1860', 'Laxå', '18', 'Örebro län'),
('1861', 'Hallsberg', '18', 'Örebro län'),
('1862', 'Degerfors', '18', 'Örebro län'),
('1863', 'Hällefors', '18', 'Örebro län'),
('1864', 'Ljusnarsberg', '18', 'Örebro län'),
('1880', 'Örebro', '18', 'Örebro län'),
('1881', 'Kumla', '18', 'Örebro län'),
('1882', 'Askersund', '18', 'Örebro län'),
('1883', 'Karlskoga', '18', 'Örebro län'),
('1884', 'Nora', '18', 'Örebro län'),
('1885', 'Lindesberg', '18', 'Örebro län');

-- Västmanlands län (10 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('1904', 'Skinnskatteberg', '19', 'Västmanlands län'),
('1907', 'Surahammar', '19', 'Västmanlands län'),
('1960', 'Kungsör', '19', 'Västmanlands län'),
('1961', 'Hallstahammar', '19', 'Västmanlands län'),
('1962', 'Norberg', '19', 'Västmanlands län'),
('1980', 'Västerås', '19', 'Västmanlands län'),
('1981', 'Sala', '19', 'Västmanlands län'),
('1982', 'Fagersta', '19', 'Västmanlands län'),
('1983', 'Köping', '19', 'Västmanlands län'),
('1984', 'Arboga', '19', 'Västmanlands län');

-- Dalarnas län (15 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('2021', 'Vansbro', '20', 'Dalarnas län'),
('2023', 'Malung-Sälen', '20', 'Dalarnas län'),
('2026', 'Gagnef', '20', 'Dalarnas län'),
('2029', 'Leksand', '20', 'Dalarnas län'),
('2031', 'Rättvik', '20', 'Dalarnas län'),
('2034', 'Orsa', '20', 'Dalarnas län'),
('2039', 'Älvdalen', '20', 'Dalarnas län'),
('2061', 'Smedjebacken', '20', 'Dalarnas län'),
('2062', 'Mora', '20', 'Dalarnas län'),
('2080', 'Falun', '20', 'Dalarnas län'),
('2081', 'Borlänge', '20', 'Dalarnas län'),
('2082', 'Säter', '20', 'Dalarnas län'),
('2083', 'Hedemora', '20', 'Dalarnas län'),
('2084', 'Avesta', '20', 'Dalarnas län'),
('2085', 'Ludvika', '20', 'Dalarnas län');

-- Gävleborgs län (10 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('2101', 'Ockelbo', '21', 'Gävleborgs län'),
('2104', 'Hofors', '21', 'Gävleborgs län'),
('2121', 'Ovanåker', '21', 'Gävleborgs län'),
('2132', 'Nordanstig', '21', 'Gävleborgs län'),
('2161', 'Ljusdal', '21', 'Gävleborgs län'),
('2180', 'Gävle', '21', 'Gävleborgs län'),
('2181', 'Sandviken', '21', 'Gävleborgs län'),
('2182', 'Söderhamn', '21', 'Gävleborgs län'),
('2183', 'Bollnäs', '21', 'Gävleborgs län'),
('2184', 'Hudiksvall', '21', 'Gävleborgs län');

-- Västernorrlands län (7 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('2260', 'Ånge', '22', 'Västernorrlands län'),
('2262', 'Timrå', '22', 'Västernorrlands län'),
('2280', 'Härnösand', '22', 'Västernorrlands län'),
('2281', 'Sundsvall', '22', 'Västernorrlands län'),
('2282', 'Kramfors', '22', 'Västernorrlands län'),
('2283', 'Sollefteå', '22', 'Västernorrlands län'),
('2284', 'Örnsköldsvik', '22', 'Västernorrlands län');

-- Jämtlands län (8 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('2303', 'Ragunda', '23', 'Jämtlands län'),
('2305', 'Bräcke', '23', 'Jämtlands län'),
('2309', 'Krokom', '23', 'Jämtlands län'),
('2313', 'Strömsund', '23', 'Jämtlands län'),
('2321', 'Åre', '23', 'Jämtlands län'),
('2326', 'Berg', '23', 'Jämtlands län'),
('2361', 'Härjedalen', '23', 'Jämtlands län'),
('2380', 'Östersund', '23', 'Jämtlands län');

-- Västerbottens län (15 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('2401', 'Nordmaling', '24', 'Västerbottens län'),
('2403', 'Bjurholm', '24', 'Västerbottens län'),
('2404', 'Vindeln', '24', 'Västerbottens län'),
('2409', 'Robertsfors', '24', 'Västerbottens län'),
('2417', 'Norsjö', '24', 'Västerbottens län'),
('2418', 'Malå', '24', 'Västerbottens län'),
('2421', 'Storuman', '24', 'Västerbottens län'),
('2422', 'Sorsele', '24', 'Västerbottens län'),
('2425', 'Dorotea', '24', 'Västerbottens län'),
('2460', 'Vännäs', '24', 'Västerbottens län'),
('2462', 'Vilhelmina', '24', 'Västerbottens län'),
('2463', 'Åsele', '24', 'Västerbottens län'),
('2480', 'Umeå', '24', 'Västerbottens län'),
('2481', 'Lycksele', '24', 'Västerbottens län'),
('2482', 'Skellefteå', '24', 'Västerbottens län');

-- Norrbottens län (14 municipalities)
INSERT INTO swedish_locations (municipality_code, municipality_name, lan_code, lan_name) VALUES
('2505', 'Arvidsjaur', '25', 'Norrbottens län'),
('2506', 'Arjeplog', '25', 'Norrbottens län'),
('2510', 'Jokkmokk', '25', 'Norrbottens län'),
('2513', 'Överkalix', '25', 'Norrbottens län'),
('2514', 'Kalix', '25', 'Norrbottens län'),
('2518', 'Övertorneå', '25', 'Norrbottens län'),
('2521', 'Pajala', '25', 'Norrbottens län'),
('2523', 'Gällivare', '25', 'Norrbottens län'),
('2560', 'Älvsbyn', '25', 'Norrbottens län'),
('2580', 'Luleå', '25', 'Norrbottens län'),
('2581', 'Piteå', '25', 'Norrbottens län'),
('2582', 'Boden', '25', 'Norrbottens län'),
('2583', 'Haparanda', '25', 'Norrbottens län'),
('2584', 'Kiruna', '25', 'Norrbottens län');
