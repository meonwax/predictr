'use strict';

angular.module('predictrApp')
  .factory('Game', function($resource) {
    return {
      // all: function() {
      //   return $resource('api/games', {}, {
      //     'query': {
      //       method: 'GET',
      //       isArray: true
      //     }
      //   });
      // },
      upcomingGames: function() {
        return $resource('api/games/upcoming', {}, {
          'query': {
            method: 'GET',
            isArray: true
          }
        });
      },
      runningGames: function() {
        return $resource('api/games/running', {}, {
          'query': {
            method: 'GET',
            isArray: true
          }
        });
      }
    }
  });
