import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

'''
definition to paginate the questions and if not possible, defaults to 1 page.
to be used later to paginate pages of questions/ category.
'''

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [questions.format() for question in selection]
    current_questions = questions[start:end]

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response


  '''
  --------- Comments: ---------
  Retrieves categories by id, if there are no categories, aborts 404(not found).
  inputs categories var for loop with format method to get model data(id, type).
  Then returns Json with required data. len counts category by querying the
  Category model.
  ---------------------------------------------------------------
  '''
  @app.route('/categories', methods=['GET'])
  def retrieve_categories():
      current_categories = Category.query.order_by(Category.id).all()

      if len(current_categories) == 0:
          abort(404)
      categories = [category.format() for category in current_category]
      return jsonify({
        "success": True,
        "categories": current_categories,
        "total_categories": len(Category.query.all())
      })

  '''
  --------- Comments: ---------
  Retrieves questions onto page by id, and then proceeds to paginate the questions
  if there are no questions, aborts 404(not found).
  Then proceeds to query and retrieve categories by id, and pushes category into
  dict, for loop for category data to get category types list.
  Afterwards proceeds to return json for required data.
  ---------------------------------------------------------------
  '''
  @app.route('/questions', methods=['GET'])
  def retrieve_questions():
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)
      if len(current_questions) == 0:
          abort(404)
      category_data = Category.query.order_by(Category.id).all()
      category_types = {}
      for category in category_data:
          category_types[str(category.id)] = category.type

      return jsonify({
        "success": True,
        "questions": current_questions,
        "total_questions": len(Question.query.all()),
        "current_category": category_types,
        "categories": Question.query.order_by(Question.category).all()
      })



  '''
  --------- Comments: ---------
  Defintion retrieves question by the question id by querying. Then deletes
  the question using the .delete() method. afterwards it queries all of the questions
  on the page and paginates the page.
  Json returns the required information.
  If there is an error, definition aborts 422 (could not be processed).
  ---------------------------------------------------------------
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
        question = Question.query.filter(Question.id == question_id).one_or_none()
        if question is None:
            abort(404)

        question.delete()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            "success": True,
            "deleted": question_id,
            "questions": current_questions,
            "total_questions": len(Question.query.all())
        })
    except:
        abort(422)



  '''
  --------- Comments: ---------
  Creates questions according to input provided by user. after the information
  is provided, it inserts the question using the (insert()) method and selects
  all questions according to question id, then proceeds to paginate the questions
  on the page.
  returns json with required information with format of the questions as per model.
  if there is an error definition aborts 422 (could not be processed).
  ---------------------------------------------------------------
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
      body = request.get_json()

      new_question = body.get('question', None)
      new_answer = body.get('answer', None)
      new_category = body.get('category', None)
      new_difficulty = body.get('difficulty', None)
      search = body.get('searchTerm')

      try:
        question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
        question.insert()

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            "success": True,
            "created": question.id,
            "questions": current_questions,
            "question": question.format(),
            "total_questions": len(Question.query.all())
            })
      except:
          abort(422)

  '''
  --------- Comments: ---------
  definition searches questions (using ilike for case-insensitive input)
  retrieves required information and paginates the page.
  if questions cannot be found - aborts 404 (not found).
  ---------------------------------------------------------------
  '''
  @app.route('/questions', methods=['POST'])
  def search_questions():
      body = request.get_json()

      try:
          selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search)))
          current_questions = paginate_questions(request, selection)
          if len(current_questions) == 0:
              abort(404)

          return jsonify({
            "success": True,
            "questions": current_questions,
            "current_category": None,
            "total_questions": len(selection.all())
          })

      except:
          abort(404)

  '''
  --------- Comments: ---------
  retrieves questions by category, first retrieves json then selects questions
  by the category according to category id and paginates the page.
  if there are no questions it aborts 404 (not found).
  retrieves according to the correct category type and returns the
  json with the required information.
  ---------------------------------------------------------------
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def questions_by_category():
      body = request.get_json()
      selection = Question.query.filter(Question.category == category_id).all()
      current_questions = paginate_questions(request, selection)

      if len(current_questions) == 0:
          abort(404)
      category = Category.query.get(category_id)
      category_type = category.type
      return jsonify({
        "success": True,
        "questions": current_questions,
        "total_questions": len(Question.query.all()),
        "current_category": category_type
        })

  '''
  --------- Comments: ---------
  Sets route for quizzes to play quizzes game with questions, makes sure to provide
  questions which have not appeard in 'previousQuestions'.
  if data cannot be found aborts 404(not found), if request not possible,
  aborts 400 (bad request).
  ---------------------------------------------------------------
  '''
  @app.route('/quizzes', methods=['POST'])
  def generate_quizzes():
    body = request.get_json()
    previousQuestions = body.get('previousQuestions', None)
    quizCategory = body.get('quizCategory', None)
    try:
        if int(quizCategory['id']) not in range(1, 7):
            abort(404)
        if quizCategory['id'] == 0:
            question = Question.query\
                       .filter(Question.id.notin_(previousQuestions))\
                       .order_by(func.random()).first()
        else:
            question = Question.query\
                       .filter(Question.category == quizCategory['id'])\
                       .filter(Question.id.notin_(previousQuestions))\
                       .order_by(func.random()).first()
        return jsonify({
            "success": True,
            "question": question.format()
        })
    except:
        abort(404)



  '''
  --------- Comments: ---------
  Sets Error handlers for 404 (not found), 422 (could not be processed),
  400 (bad request).
  Messages replace HTML standard into JSON formatting in order to provide
  symmetry between formats.
  ---------------------------------------------------------------
  '''
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
         "success": False,
         "error": 422,
         "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
      }), 400

  @app.errorhandler(405)
  def not_allowed(error):
      return jsonify({
        "success": False,
        "error", 405,
        "message": "method not allowed",
      }), 405

  return app
