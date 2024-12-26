SELECT 'CREATE DATABASE feathrregistry'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'feathrregistry')\gexec

SELECT 'CREATE DATABASE feathr_featurestore_offline'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'feathr_featurestore_offline')\gexec

