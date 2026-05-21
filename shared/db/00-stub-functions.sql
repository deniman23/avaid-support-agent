-- Stubs for DDL triggers when extensions are not installed (local mock DB)
CREATE OR REPLACE FUNCTION public.marketplace_products_search_vector_trigger()
RETURNS trigger AS $$
BEGIN
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
