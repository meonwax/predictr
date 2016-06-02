'use strict';

angular.module('predictrApp')
  .factory('Ladder', function($resource, $http) {
    return {
      ladder: function() {
        return $resource('api/ladder', {}, {
          'all': {
            method: 'GET',
            isArray: true
          },
          'jackpotOnly': {
            method: 'GET',
            params: {
              jackpot_only: 1
            },
            isArray: true
          }
        });
      }
    };
  });
