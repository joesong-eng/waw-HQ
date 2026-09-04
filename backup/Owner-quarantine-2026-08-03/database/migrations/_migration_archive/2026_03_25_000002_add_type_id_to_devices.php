<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            // 在現有 type enum 欄位之後新增 type_id，保留 type enum 向後相容
            $table->unsignedBigInteger('type_id')->nullable()->after('type');

            $table->foreign('type_id', 'fk_devices_type_id')
                ->references('id')->on('device_types')
                ->onDelete('set null');
        });
    }

    public function down(): void
    {
        Schema::table('devices', function (Blueprint $table) {
            $table->dropForeign('fk_devices_type_id');
            $table->dropColumn('type_id');
        });
    }
};
