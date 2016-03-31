'use strict';

angular.module('predictrApp')
  .factory('Group', function($resource) {
    return $resource('api/groups', {}, {
      'query': {
        method: 'GET',
        isArray: true
      }
    });
  });
