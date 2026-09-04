<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * infra 自動預註冊：新增 timezone 欄位
     * 設備上線時透過 device/{id}/info 上報，infra listener 寫入
     */
    public function up(): void
    {
        if (!Schema::hasColumn('devices', 'timezone')) {
            Schema::table('devices', function (Blueprint $table) {
                $table->string('timezone', 50)->nullable()->after('firmware_ver')->comment('設備時區，如 Asia/Taipei，由 infra listener 寫入');
            });
        }
    }

    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropColumn('timezone');
        });
    }
};
