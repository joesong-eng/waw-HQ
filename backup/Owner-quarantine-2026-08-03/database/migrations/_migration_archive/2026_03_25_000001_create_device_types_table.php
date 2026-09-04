<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('device_types', function (Blueprint $table) {
            $table->id();
            $table->string('name', 50)->unique();
            $table->unsignedBigInteger('created_by')->nullable();
            $table->timestamp('created_at')->useCurrent();

            $table->foreign('created_by')
                ->references('id')->on('users')
                ->onDelete('set null');
        });

        // Seed 預設機種
        DB::table('device_types')->insert([
            ['name' => '娃娃機', 'created_by' => null, 'created_at' => now()],
            ['name' => '彈珠台', 'created_by' => null, 'created_at' => now()],
            ['name' => '拉霸',   'created_by' => null, 'created_at' => now()],
            ['name' => '水果台', 'created_by' => null, 'created_at' => now()],
        ]);
    }

    public function down(): void
    {
        Schema::dropIfExists('device_types');
    }
};
