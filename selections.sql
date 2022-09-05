/* название и год выхода альбомов, вышедших в 2018 году */
SELECT album_title, album_year FROM albums
WHERE album_year = 2018;

/* название и продолжительность самого длительного трека */
SELECT track_title, duration FROM tracks 
ORDER BY duration DESC LIMIT 1;

/* название треков, продолжительность которых не менее 3,5 минуты */
SELECT track_title FROM tracks
WHERE duration > 3.5 * 60;

/* названия сборников, вышедших в период с 2018 по 2020 год включительно */
SELECT album_title FROM albums
WHERE album_year IN (2018, 2019, 2020);

/* исполнители, чье имя состоит из 1 слова */
SELECT alias FROM artists
WHERE alias NOT LIKE '% %';

/* название треков, которые содержат слово "мой"/"my" */
SELECT track_title FROM tracks
WHERE LOWER(track_title) LIKE '%мой%' OR LOWER(track_title) LIKE '%my%';
