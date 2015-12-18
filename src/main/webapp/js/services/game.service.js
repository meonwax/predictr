'use strict';

angular.module('predictrApp')
  .factory('Game', function($resource) {
    return {
      games: function() {
        return $resource('api/games', {}, {
          'get': {
            method: 'GET',
            isArray: true,
            transformResponse: function (data) {
              return angular.fromJson(data);
            }
          }
        });
      },
      upcomingGames: function() {
        return $resource('/api/games/upcoming', {}, {
          'get': {
            method: 'GET',
            isArray: true,
            transformResponse: function (data) {
              return angular.fromJson(data);
            }
          }
        });
      },
      runningGames: function() {
        return $resource('/api/games/running', {}, {
          'get': {
            method: 'GET',
            isArray: true,
            transformResponse: function (data) {
              return angular.fromJson(data);
            }
          }
        });
      }
    }
  });
