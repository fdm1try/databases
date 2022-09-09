/* количество исполнителей в каждом жанре */
SELECT g.genre_title, count(a.artist_id) c FROM artist_genres ag 
RIGHT JOIN artists a ON a.artist_id = ag.artist_id 
RIGHT JOIN genres g ON g.genre_id = ag.genre_id
GROUP BY g.genre_title
ORDER BY c DESC;

/* количество треков, вошедших в альбомы 2019-2020 годов */
SELECT count(track_id) FROM albums
JOIN tracks ON tracks.album_id = albums.album_id 
WHERE album_year IN (2019,2020);
 
/* средняя продолжительность треков по каждому альбому */
SELECT a.album_title, AVG(t.duration) FROM tracks t 
JOIN albums a ON a.album_id = t.album_id 
GROUP BY a.album_title
ORDER BY a.album_title;

/* все исполнители, которые не выпустили альбомы в 2020 году */
SELECT artists.alias FROM (
	SELECT aa.artist_id FROM album_artists aa 
	JOIN albums a ON aa.album_id = a.album_id 
	WHERE a.album_year = 2020
) a
RIGHT JOIN artists ON artists.artist_id = a.artist_id 
WHERE a.artist_id IS NULL;

/* названия сборников, в которых присутствует конкретный исполнитель (выберите сами) */
SELECT DISTINCT c.collection_title FROM (
	SELECT t.track_id FROM album_artists aa 
	JOIN artists a ON a.artist_id = aa.artist_id
	JOIN tracks t ON t.album_id = aa.album_id
	WHERE a.alias = 'Eminem'
) t
JOIN collection_tracks ct ON t.track_id = ct.track_id 
JOIN collections c ON c.collection_id = ct.collection_id;

/* название альбомов, в которых присутствуют исполнители более 1 жанра */
SELECT albums.album_title FROM (
	SELECT a.artist_id FROM artists a 
	JOIN artist_genres ag ON ag.artist_id = a.artist_id 
	GROUP BY a.artist_id  
	HAVING COUNT(ag.genre_id) > 1
) a
JOIN album_artists aa ON a.artist_id = aa.artist_id 
JOIN albums ON albums.album_id = aa.album_id;

/* наименование треков, которые не входят в сборники */
SELECT t.track_title FROM collection_tracks ct 
RIGHT JOIN tracks t ON t.track_id = ct.track_id 
WHERE ct.track_id IS NULL;

/* исполнителя(-ей), написавшего самый короткий по продолжительности трек (теоретически таких треков может быть несколько) */
SELECT a.alias FROM (
	SELECT MIN(duration) min_duration FROM tracks
) x 
JOIN tracks t ON x.min_duration = t.duration 
JOIN album_artists aa ON aa.album_id = t.album_id 
JOIN artists a ON aa.artist_id = a.artist_id;

/* название альбомов, содержащих наименьшее количество треков. */
WITH track_count AS (
	SELECT count(track_id) cnt, album_id FROM tracks
	GROUP BY album_id
)
SELECT albums.album_title FROM track_count
JOIN albums ON albums.album_id = track_count.album_id
WHERE cnt = (SELECT min(cnt) FROM track_count)


