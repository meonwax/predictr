'use strict';

angular.module('predictrApp')
  .factory('Shout', function($resource) {
    return $resource('api/shouts');
  });
