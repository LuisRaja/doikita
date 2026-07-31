-- Run this SQL in your Supabase SQL Editor (https://app.supabase.com > SQL Editor)

-- 1. Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    "user" TEXT NOT NULL CHECK ("user" IN ('LUIS', 'HESTI')),
    "type" TEXT NOT NULL CHECK ("type" IN ('pemasukan', 'pengeluaran')),
    category TEXT NOT NULL CHECK (category IN ('bisnis', 'pribadi')),
    amount BIGINT NOT NULL CHECK (amount > 0),
    description TEXT DEFAULT '',
    owner_pribadi TEXT CHECK (owner_pribadi IS NULL OR owner_pribadi IN ('LUIS', 'HESTI'))
);

-- 2. Saldo table
CREATE TABLE IF NOT EXISTS saldo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kategori TEXT UNIQUE NOT NULL CHECK (kategori IN ('bisnis', 'pribadi_LUIS', 'pribadi_HESTI')),
    saldo BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Insert default saldo rows
INSERT INTO saldo (kategori, saldo) VALUES
    ('bisnis', 0),
    ('pribadi_LUIS', 0),
    ('pribadi_HESTI', 0)
ON CONFLICT (kategori) DO NOTHING;

-- 3. Rekapan table
CREATE TABLE IF NOT EXISTS rekapan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    bulan INT NOT NULL CHECK (bulan >= 1 AND bulan <= 12),
    tahun INT NOT NULL,
    "user" TEXT NOT NULL CHECK ("user" IN ('LUIS', 'HESTI')),
    total_masuk BIGINT NOT NULL DEFAULT 0,
    total_keluar BIGINT NOT NULL DEFAULT 0,
    saldo_akhir BIGINT NOT NULL DEFAULT 0,
    pdf_link TEXT,
    UNIQUE (bulan, tahun, "user")
);

-- Enable Row Level Security (optional)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE saldo ENABLE ROW LEVEL SECURITY;
ALTER TABLE rekapan ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (since using service_role key)
CREATE POLICY "Allow all on transactions" ON transactions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on saldo" ON saldo FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on rekapan" ON rekapan FOR ALL USING (true) WITH CHECK (true);
