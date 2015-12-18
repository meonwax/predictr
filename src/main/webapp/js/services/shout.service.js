'use strict';

angular.module('predictrApp')
  .factory('Shout', function($resource) {
    return $resource('api/shouts/:id', {}, {
      'query': {
        method: 'GET',
        isArray: true
      },
      'get': {
        method: 'GET',
        transformResponse: function (data) {
          return angular.fromJson(data);
        }
      }
    });
  });
