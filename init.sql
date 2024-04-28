DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'books'
  ) THEN
    CREATE DATABASE books;
  END IF;
END $$;

\c books;