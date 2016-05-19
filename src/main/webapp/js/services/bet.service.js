'use strict';

angular.module('predictrApp')
  .factory('Bet', function($resource) {
    return $resource('api/bets');
  });
