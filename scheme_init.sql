DROP TABLE IF EXISTS album_artists;
DROP TABLE IF EXISTS artist_genres;
DROP TABLE IF EXISTS collection_tracks;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS tracks;
DROP TABLE IF EXISTS albums;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS collections;

CREATE TABLE IF NOT EXISTS albums (
	album_id SERIAL PRIMARY KEY,
	album_title VARCHAR(100) NOT NULL,
	album_year INTEGER NOT NULL,
	CHECK (album_year > 1859)
);

CREATE TABLE IF NOT EXISTS tracks (
	track_id SERIAL PRIMARY KEY,
	track_title VARCHAR(100) NOT NULL,
	duration INTEGER NOT NULL,
	CHECK (duration > 0),
	album_id INTEGER REFERENCES albums
);

CREATE TABLE IF NOT EXISTS artists (
	artist_id SERIAL PRIMARY KEY,
	alias VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS genres (
	genre_id SERIAL PRIMARY KEY,
	genre_title VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS collections (
	collection_id SERIAL PRIMARY KEY,
	collection_title VARCHAR(100) NOT NULL,
	collection_year INTEGER NOT NULL,
	CHECK (collection_year > 1859)
);

CREATE TABLE IF NOT EXISTS album_artists (
	album_id INTEGER REFERENCES albums,
	artist_id INTEGER REFERENCES artists,
	CONSTRAINT pk_album_artists PRIMARY KEY (album_id, artist_id)
);

CREATE TABLE IF NOT EXISTS artist_genres (
	artist_id INTEGER REFERENCES artists,
	genre_id INTEGER REFERENCES genres,
	CONSTRAINT pk_artist_genres PRIMARY KEY (artist_id, genre_id)
);

CREATE TABLE IF NOT EXISTS collection_tracks (
	collection_id INTEGER REFERENCES collections,
	track_id INTEGER REFERENCES tracks,
	CONSTRAINT pk_collection_tracks PRIMARY KEY (collection_id, track_id)
);