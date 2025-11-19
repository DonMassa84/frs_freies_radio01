import '../models/schedule_entry.dart';
import '../models/media_entry.dart';
import 'schedule_service.dart';
import 'mediathek_service.dart';

class FrsApi {
  static Future<List<ScheduleEntry>> getTodaySchedule() =>
      ScheduleService.loadToday();

  static Future<List<MediaEntry>> getMediathekArchive() =>
      MediathekService.loadArchive();
}
