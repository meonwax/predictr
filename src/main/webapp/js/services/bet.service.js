'use strict';

angular.module('predictrApp')
  .factory('Bet', function($resource) {
    return $resource('api/bets/:id', {}, {
      'query': {
        method: 'GET',
        isArray: true
      },
      'save': {
        method:'POST'
      }
    });
  });
