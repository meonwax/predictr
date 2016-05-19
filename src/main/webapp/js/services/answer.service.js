'use strict';

angular.module('predictrApp')
  .factory('Answer', function ($resource) {
    return $resource('api/answers');
  });
