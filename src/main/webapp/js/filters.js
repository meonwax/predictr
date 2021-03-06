'use strict';

angular.module('predictrApp')
  .filter('myDate', function($filter, $translate) {
    return function(timestamp) {
      var date = $filter('amDateFormat')(timestamp * 1000, 'lll z');
      return timezoneTranslator($translate, date);
    };
  })
  .filter('myDateShort', function($filter) {
    return function(timestamp) {
      return $filter('amDateFormat')(timestamp * 1000, 'L LT');
    };
  })
  .filter('myDateLong', function($filter, $translate) {
    return function(timestamp) {
      var date = $filter('amDateFormat')(timestamp * 1000, 'll LTS z');
      return timezoneTranslator($translate, date);
    };
  })
  .filter('playTime', function() {
    return function(timestamp) {
      var diffSeconds = Date.now() / 1000 - timestamp;
      var diffMinutes = Math.floor(diffSeconds / 60);
      var diffHours = Math.floor(diffMinutes / 60);
      return diffHours + ':' + ('0' + (diffMinutes - diffHours * 60)).slice(-2) + 'h';
    };
  })
  .filter('bet', function($filter) {
    return function(bet) {
      return bet ? bet.scoreHome + ':' + bet.scoreAway : null;
    };
  })
  .filter('rank', function($filter) {
    return function(rank) {
      return rank ? rank + '.' : '';
    };
  });

var timezoneTranslator = function($translate, date) {
  switch($translate.use()) {
    case 'de':
      return date.replace(new RegExp("CEST", 'g'), "MESZ");
    default:
      return date;
  }
};
