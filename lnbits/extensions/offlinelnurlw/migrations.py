def m001_initial(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS offlinelnurlw_link (
            id TEXT PRIMARY KEY,
            wallet TEXT,
            title TEXT,
            private_key TEXT,
            amount INT,
            used INTEGER DEFAULT 0,
            time TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
        );
    """
    )

