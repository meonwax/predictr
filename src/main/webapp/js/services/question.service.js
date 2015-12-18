'use strict';

angular.module('predictrApp')
  .factory('Question', function ($resource) {
    return $resource('api/questions', {}, {
      'query': {
        method: 'GET',
        isArray: true
      }
    });
  });
