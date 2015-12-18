'use strict';

angular.module('predictrApp')
  .filter('myDate', function($filter) {
    return function(timestamp) {
      return $filter('date')(timestamp * 1000, 'yyyy-MM-dd HH:mm:ss \'GMT\' Z');
    };
  })
  .filter('myDateShort', function($filter) {
    return function(timestamp) {
      return $filter('date')(timestamp * 1000, 'MM-dd HH:mm');
    };
  })
  .filter('playTime', function() {
    return function(timestamp) {
      var diffSeconds = Date.now() / 1000 - timestamp;
      var diffMinutes = Math.floor(diffSeconds / 60);
      var diffHours = Math.floor(diffMinutes / 60);
      return diffHours + ':' + ('0' + (diffMinutes - diffHours * 60)).slice(-2);
    };
  });
