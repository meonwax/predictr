'use strict';

angular.module('predictrApp')
  .factory('Team', function($resource) {
    return $resource('api/teams');
  });
