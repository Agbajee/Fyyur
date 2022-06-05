#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import datetime
from models import dbConnect, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = dbConnect(app)

# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  venue_areas = db.session.query(Venue.city,Venue.state).group_by(Venue.state, Venue.city).all()
  data = []
  for area in venue_areas:
    venues = db.session.query(Venue.id,Venue.name, Venue.num_upcoming_shows).filter(Venue.city==area[0],Venue.state==area[1]).all()
    data.append({
        "city": area[0],
        "state": area[1],
        "venues": []
    })
    for venue in venues:
      data[-1]["venues"].append({
              "id": venue[0],
              "name": venue[1],
              "num_upcoming_shows":venue[2]
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  venue_results = Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()
  response={
    "count": len(venue_results),
    "data": []
    }
  for venue in venue_results:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": venue.num_upcoming_shows
      })
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  today = datetime.datetime.now()

  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<today).all()
  past_shows = []
  for show in past_shows_query:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    })


  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>today).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      })

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')
    venue.website = request.form['website_link']
    venue.image_link = request.form['image_link']
    venue.seeking_talent = request.form.get('seeking_talent', type=bool)
    venue.seeking_description = request.form['seeking_description']

    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue_id = request.form.get('venue_id')
    Venue.query.filter_by(id=venue_id).delete()

    db.session.commit()
    flash(' Venue deleted successfully!')
  except:
    db.session.rollback()
    flash('Error! venue could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data= Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  results = Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()

  response={
    "count": len(results),
    "data": []
  }
  for artist in results:
    response['data'].append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": artist.num_upcoming_shows,
      })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = db.session.query(Artist).get(artist_id)
  today = datetime.datetime.now()

  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time<today).all()
  past_shows = []
  for show in past_shows_query:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time)
    })

  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time>today).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      })
      
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres, 
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description":artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  details= Artist.query.get(artist_id)
  artist={
    "id": details.id,
    "name": details.name,
    "genres": [details.genres],
    "city": details.city,
    "state": details.state,
    "phone": details.phone,
    "website": details.website,
    "facebook_link": details.facebook_link,
    "seeking_venue": details.seeking_venue,
    "seeking_description": details.seeking_description,
    "image_link": details.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = request.form.get('seeking_venue', type=bool)
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
    flash("Artist {} is updated successfully".format(artist.name))
  except:
    db.session.rollback()
    flash("Artist {} isn't updated successfully".format(artist.name))
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  details= Venue.query.get(venue_id)
  venue={
    "id": details.id,
    "name": details.name,
    "genres": [details.genres],
    "city": details.city,
    "state": details.state,
    "phone": details.phone,
    "website": details.website,
    "facebook_link": details.facebook_link,
    "seeking_talent": details.seeking_talent,
    "seeking_description": details.seeking_description,
    "image_link": details.image_link
  }
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.website = request.form['website_link']
    venue.seeking_venue = request.form.get('seeking_venue', type=bool)
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
    flash("Venue {} is updated successfully".format(venue.name))
  except:
    db.session.rollback()
    flash("Venue {} isn't updated successfully".format(venue.name))
  finally:
    db.session.close()
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  try:
    artist = Artist()
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.genres = request.form.getlist('genres')
    artist.phone = request.form['phone']
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = request.form.get('seeking_venue', type=bool)
    artist.seeking_description = request.form['seeking_description']

    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.

  shows = Show.query.all()
  data = []
  
  for show in shows:
    if(show.upcoming_show):
      data=[{
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time),
        }]

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    show = Show()
    show.venue_id=request.form['venue_id'],
    show.artist_id=request.form['artist_id'],
    show.start_time=request.form['start_time'],
      
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
