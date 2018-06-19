'use strict';

angular.module('predictrApp')
  .factory('Answer', function ($resource) {
    return $resource('api/answers/:questionId', {}, {
      'query': {
        method: 'GET',
        isArray: true
      },
      'save': {
        method:'POST'
      }
    });
  });
