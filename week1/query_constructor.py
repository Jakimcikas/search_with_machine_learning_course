

class QueryConstructor:
    """
    Basic query construction class
    Thought I might construct a proper query building class, but that just takes too much time
    So was left with a semi-reasuable constructor, maybe I'll finish this as the course goes
    But currently it's at a terrible state :(
    """
    def __init__(self):
        self._elastic_query = {}
        self._aggs = {}
        self._source = []
    
    def limit_source(self):
        self._source = [
            "productId",
            "name",
            "shortDescription",
            "longDescription",
            "department",
            "salesRankShortTerm",
            "salesRankMediumTerm",
            "salesRankLongTerm",
            "regularPrice",
            "categoryPath",
            "image"
            ]
        
        return self

    def match_all(self):
        self._elastic_query["match_all"] = {}
        return self 

    def bool_query(self):
        self._elastic_query["bool"] = {
            "must": [],
            "filter": [],
            "should": [],
            "must_not": [],
        }

        return self

    def query_string(self, query_input, clause):
        query_string_dict = {
            "query_string": {
                "query": query_input,
                "fields": ["name^1000", "shortDescription^50", "longDescription^10", "department"]
            }
        }

        self._elastic_query["bool"][clause].append(query_string_dict)
        return self

    def apply_filters(self, filters):
        if len(filters) == 0:
            return self
        
        for f in filters:
            if "terms" in f:
                self._add_terms_filter(f["terms"])
            elif "range" in f:
                self._add_range_filter(f["range"])
        
        return self

    def _add_terms_filter(self, filter):
        filter_dict = {
            "term": {
                filter["field"]: filter["value"]
            }
        }

        self._elastic_query["bool"]["filter"].append(filter_dict)

    def _add_range_filter(self, filter):
        field = filter["field"]

        filter_dict = {
            "range": {
                field: {}
            }
        }

        if filter["from"]:
            filter_dict["range"][field]["gte"] = filter["from"]

        if filter["to"]:
            filter_dict["range"][field]["lt"] = filter["to"]

        self._elastic_query["bool"]["filter"].append(filter_dict)

    def missing_image_aggs(self):
        self._aggs["missing_images"] = {
            "missing": {
                "field": "image"
            }
        }
    
        return self

    def department_aggs(self):
        self._aggs["departments"] = {
            "terms": {
                "field": "department.keyword",
                "size": 10
            }
        }

        return self
    
    def range_aggs(self):
        self._aggs["regularPrice"] = {
            "range": {
                "field": "regularPrice",
                "ranges": [
                    {
                        "to": 10,
                        "key": "$"
                    },
                    {
                        "from": 10,
                        "to": 100,
                        "key": "$$"
                    },
                    {
                        "from": 100,
                        "to": 1000,
                        "key": "$$$"
                    },
                    {
                        "from": 1000,
                        "to": 10000,
                        "key": "$$$$"
                    },
                    {
                        "from": 10000,
                        "key": "$$$$$$"
                    }
                ]
            }
        }

        return self

    def _functions(self):
        return [
        {
          "field_value_factor": {
            "field": "salesRankShortTerm",
            "missing": 100000000,
            "modifier": "reciprocal"
          }
        },
        {
          "field_value_factor": {
            "field": "salesRankLongTerm",
            "missing": 100000000,
            "modifier": "reciprocal"
          }
        },
        {
          "field_value_factor": {
            "field": "salesRankMediumTerm",
            "missing": 100000000,
            "modifier": "reciprocal"
          }
        }
      ]

    def _function_query(self):
        return {
            "function_score": {
                "query": self._elastic_query,
                "functions": self._functions(),
                "boost_mode": "replace",
                "score_mode": "avg"
            }
        }

    def build(self):
        return {
            "_source": self._source,
            "query": self._elastic_query,
            "aggs": self._aggs
        }

    def build_function_query(self):
        return {
            "_source": self._source,
            "query": self._elastic_query,
            "aggs": self._aggs
        }

