<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('system_settings', function (Blueprint $table) {
            $table->id();
            $table->string('key', 100)->unique()->comment('設定鍵名');
            $table->text('value')->nullable()->comment('設定值');
            $table->string('type', 20)->default('string')->comment('資料類型: string, integer, boolean, json');
            $table->text('description')->nullable()->comment('設定說明');
            $table->timestamps();
            
            $table->index('key');
        });

        // 插入預設的 Session 超時設定
        DB::table('system_settings')->insert([
            [
                'key' => 'device_session_inactivity_timeout',
                'value' => '120',
                'type' => 'integer',
                'description' => '遊戲機 Session 無活動超時時長（秒）',
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'key' => 'device_session_absolute_timeout',
                'value' => '1200',
                'type' => 'integer',
                'description' => '遊戲機 Session 絕對超時時長（秒）',
                'created_at' => now(),
                'updated_at' => now(),
            ],
        ]);
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('system_settings');
    }
};
