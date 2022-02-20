#
# The main search hooks for the Search Flask application.
#
from flask import (
    Blueprint, redirect, render_template, request, url_for
)

from week1.opensearch import get_opensearch
from week1.query_constructor import QueryConstructor

bp = Blueprint('search', __name__, url_prefix='/search')

index_name = "bbuy_products"

debug = False


# Process the filters requested by the user and return a tuple that is appropriate for use in: the query, URLs displaying the filter and the display of the applied filters
# filters -- convert the URL GET structure into an OpenSearch filter query
# display_filters -- return an array of filters that are applied that is appropriate for display
# applied_filters -- return a String that is appropriate for inclusion in a URL as part of a query string.  This is basically the same as the input query string
def process_filters(filters_input):
    # Filters look like: &filter.name=regularPrice&regularPrice.key={{ agg.key }}&regularPrice.from={{ agg.from }}&regularPrice.to={{ agg.to }}
    filters = []
    display_filters = []  # Also create the text we will use to display the filters that are applied
    applied_filters = ""
    for filter in filters_input:
        type = request.args.get(filter + ".type")
        display_name = request.args.get(filter + ".displayName", filter)

        # filters get used in create_query below.  display_filters gets used by display_filters.jinja2 and applied_filters gets used by aggregations.jinja2 (and any other links that would execute a search.)
        if type == "range":
            f, applied_filter = range_filter(request.args, filter)
            filters.append(f)
            applied_filters += applied_filter
        elif type == "terms":
            f, applied_filter = terms_filter(request.args, filter)
            filters.append(f)
            applied_filters += applied_filter

    print("Filters: {}".format(filters))
    print(f"filter input: {filters_input}")
    print(f"applied filters: {applied_filters}")
    print(f"request args: {request.args}")

    return filters, display_filters, applied_filters


# Our main query route.  Accepts POST (via the Search box) and GETs via the clicks on aggregations/facets
@bp.route('/query', methods=['GET', 'POST'])
def query():
    opensearch = get_opensearch() # Load up our OpenSearch client from the opensearch.py file.
    # Put in your code to query opensearch.  Set error as appropriate.
    error = None
    user_query = None
    query_obj = None
    display_filters = None
    applied_filters = ""
    filters = None
    sort = "_score"
    sortDir = "desc"
    if request.method == 'POST':  # a query has been submitted
        user_query = request.form['query']
        if not user_query:
            user_query = "*"
        sort = request.form["sort"]
        if not sort:
            sort = "_score"
        sortDir = request.form["sortDir"]
        if not sortDir:
            sortDir = "desc"
        query_obj = create_query(user_query, [], sort, sortDir)
    elif request.method == 'GET':  # Handle the case where there is no query or just loading the page
        user_query = request.args.get("query", "*")
        filters_input = request.args.getlist("filter.name")
        sort = request.args.get("sort", sort)
        sortDir = request.args.get("sortDir", sortDir)
        if filters_input:
            (filters, display_filters, applied_filters) = process_filters(filters_input)

        query_obj = create_query(user_query, filters, sort, sortDir)
    else:
        query_obj = create_query("*", [], sort, sortDir)
    
    response = opensearch.search( body = query_obj, index = index_name )
    
    if debug:
        print(f"response: {response}")
    # Postprocess results here if you so desire

    #print(response)
    if error is None:
        return render_template("search_results.jinja2", query=user_query, search_response=response,
                               display_filters=display_filters, applied_filters=applied_filters,
                               sort=sort, sortDir=sortDir)
    else:
        redirect(url_for("index"))


def create_query(user_query, filters, sort="_score", sortDir="desc"):
    print("Query: {} Filters: {} Sort: {}".format(user_query, filters, sort))

    if user_query == "*":
        return QueryConstructor() \
        .match_all() \
        .range_aggs() \
        .missing_image_aggs() \
        .department_aggs() \
        .build()

    query_obj = QueryConstructor().limit_source() \
        .bool_query() \
        .query_string(user_query, "must") \
        .apply_filters(filters) \
        .range_aggs() \
        .missing_image_aggs() \
        .department_aggs() \
        .build_function_query()

    if debug:
        print("query obj: {}".format(query_obj))

    return query_obj

def range_filter(args, filter_name):
    range_from = args.get(f"{filter_name}.from", '')
    range_to = args.get(f"{filter_name}.to", '')
    display_name = request.args.get(filter_name + ".displayName", filter_name)
    
    if not range_from and not range_to:
        return {}

    applied_filter = f"&filter.name={filter_name}&{filter_name}.type=range" \
        + f"&{filter_name}.displayName={display_name}&{filter_name}.from={range_from}&{filter_name}.to={range_to}"

    range_filter = {
        "range": {
            "field": filter_name,
            "from": range_from,
            "to": range_to
        }
    }

    return range_filter, applied_filter

def terms_filter(args, filter_name):
    term_value = args.get(f"{filter_name}.key", '')
    display_name = args.get(filter_name + ".displayName", filter_name)

    if not term_value:
        return {}

    term_filter = {
        "terms": {
            "field": f"{filter_name}.keyword",
            "value": term_value
        }
    }

    applied_filter = f"&filter.name={filter_name}&{filter_name}.type=terms" \
        + f"&{filter_name}.displayName={display_name}&{filter_name}.key={term_value}"

    return term_filter, applied_filter
