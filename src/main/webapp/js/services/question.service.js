'use strict';

angular.module('predictrApp')
  .factory('Question', function ($resource) {
    return {
      all: function() {
        return $resource('api/questions', {}, {
          'query': {
            method: 'GET',
            isArray: true
          }
        });
      },
      deadlinePassed(question) {
        return (new Date() > new Date(question.deadline * 1000));
      }
    }
  });
