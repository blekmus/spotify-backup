# Spotify Backup Script

Saves spotify data into csv files. Optionally upload to Backblaze B2 bucket.

## File Structure
~~~
Music/
├── Playlists/
│   ├── User/
│   │   └── ...
│   ├── Foreign/
│   │   └── ...
│   ├── UserPlaylists.csv
│   └── ForeignPlaylists.csv
├── Liked.csv
├── Albums.csv
└── Artists.csv

Podcasts/
├── Episodes.csv
└── Shows.csv
~~~
~~~markdown
# Liked tracks
Music/Playlists/Liked.csv

# Liked albums
Music/Playlists/Albums.csv

# Followed artists
Music/Playlists/Artists.csv

# Details about playlists created by the user
Music/Playlists/UserPlaylists.csv

# Details about liked playlists
Music/Playlists/ForeignPlaylists.csv

# Songs of playlists created by the user
# Each playlist is seperated into a single csv file
Music/Playlists/User/...

# Songs of liked playlists
# Each playlist is seperated into a single csv file
Music/Playlists/Foreign/...
~~~
~~~markdown
# Saved episodes
Podcasts/Episodes.csv

# Followed shows
Podcasts/Shows.csv
~~~

## CSV Formats (columns)

### Music

~~~markdown
# Liked.csv

Track ID,
Album ID,
Track Name,
Album Name,
Artists,
Release Date,
Duration (ms),
Explicity,
Album Type,
Popularity,
Added On,
Album Tracks,
Track URL,
Album URL
~~~
~~~markdown
# Albums.csv

ID,
Name,
Tracks,
Artists,
Release Date,
Label,
Type,
Popularity,
Added On,
URL
~~~

~~~markdown
# Artists.csv

ID,
Name,
Type,
Followers,
Popularity,
URL
~~~
~~~markdown
# ForeignPlaylists.csv
# UserPlaylists.csv

ID,
Spotify URI,
Name,
Description,
Tracks,
URL
~~~
~~~markdown
# User/...
# Foreign/...

Track ID,
Album ID,
Track Name,
Album Name,
Artists,
Release Date,
Duration (ms),
Explicity,
Album Type,
Popularity,
Added On,
Album Tracks,
Track URL,
Album URL
~~~

### Podcasts

~~~markdown
# Episodes.csv

Episode ID,
Show ID,
Episode Name,
Show Name,
Publisher,
Description,
Release Date,
Duration (ms),
Explicity,
Show Type,
Added On,
Episode URL,
Show URL
~~~
~~~markdown
# Shows.csv

ID,
Name,
Publisher,
Description,
Episodes,
Type,
Explicity,
Added On,
URL
~~~