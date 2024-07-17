CREATE TABLE changelogs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    api_keys TEXT NOT NULL,
    doc_url TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);
